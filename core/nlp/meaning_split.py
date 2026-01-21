import concurrent.futures
import math
from difflib import SequenceMatcher

import jieba
from loguru import logger
from rich.table import Table

from core.nlp.nlp_split import load_spacy_model
from core.utils.common import get_joiner
from core.utils.llm import ask_llm
from core.utils.prompts import get_split_prompt


def process_meaning_split(sentences: list, source_language: str = "en") -> list:
    """
    流水线第四步：AI 语义分割

    Args:
        sentences: NLP 分割结果文件路径
        source_language: 源语言代码

    Returns:
        分割结果文件路径
    """
    logger.info("Starting meaning split with AI")
    # 检测语言，中文使用 jieba 进行 tokenization
    use_jieba = source_language == "zh"

    if use_jieba:
        logger.warning("Using jieba for Chinese tokenization in meaning split")
        nlp = None
    else:
        nlp = load_spacy_model(source_language)

    # process sentences multiple times to ensure all are split
    sentences = parallel_split_sentences(
        sentences, language=source_language, nlp=nlp, use_jieba=use_jieba, max_length=10
    )

    return sentences


def parallel_split_sentences(
    sentences: list, language: str, nlp=None, max_length: int = 42, use_jieba: bool = False
) -> list:
    """Split sentences in parallel using a thread pool."""
    new_sentences = [None] * len(sentences)
    futures = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        for index, sentence in enumerate(sentences):
            # Use tokenizer to split the sentence (jieba for Chinese, Spacy for others)
            tokens = tokenize_sentence(sentence, nlp, use_jieba=use_jieba)
            # print("Tokenization result:", tokens)
            num_parts = math.ceil(len(tokens) / max_length)
            if len(tokens) > max_length:
                future = executor.submit(split_sentence, sentence, num_parts, max_length, index=index, retry_attempt=3)
                futures.append((future, index, num_parts, sentence))
            else:
                new_sentences[index] = [sentence]

        for future, index, _num_parts, sentence in futures:
            split_result = future.result()
            if split_result:
                split_lines = split_result.strip().split("\n")
                new_sentences[index] = [line.strip() for line in split_lines]
            else:
                new_sentences[index] = [sentence]

    return [sentence for sublist in new_sentences for sentence in sublist]


def tokenize_sentence(sentence: str, nlp, use_jieba: bool = False):
    """Tokenize a sentence using Spacy or jieba (for Chinese)"""
    if use_jieba:
        return list(jieba.cut(sentence))
    else:
        doc = nlp(sentence)
        return [token.text for token in doc]


def split_sentence(sentence, num_parts, word_limit=20, index=-1, retry_attempt=0):
    """Split a long sentence using GPT and return the result as a string."""
    split_prompt = get_split_prompt(sentence, num_parts, word_limit)

    def valid_split(response_data):
        choice = response_data["choice"]
        if f"split{choice}" not in response_data:
            return {"status": "error", "message": "Missing required key: `split`"}
        if "[br]" not in response_data[f"split{choice}"]:
            return {"status": "error", "message": "Split failed, no [br] found"}
        return {"status": "success", "message": "Split completed"}

    response_dict = ask_llm(split_prompt + " " * retry_attempt, log_title="split_by_meaning")
    choice = response_dict["choice"]
    best_split = response_dict[f"split{choice}"]
    split_points = find_split_positions(sentence, best_split)
    # split the sentence based on the split points
    for i, split_point in enumerate(split_points):
        if i == 0:
            best_split = sentence[:split_point] + "\n" + sentence[split_point:]
        else:
            parts = best_split.split("\n")
            last_part = parts[-1]
            parts[-1] = (
                last_part[: split_point - split_points[i - 1]] + "\n" + last_part[split_point - split_points[i - 1] :]
            )
            best_split = "\n".join(parts)
    if index != -1:
        print(f"[green]✅ Sentence {index} has been successfully split[/green]")
    table = Table(title="")
    table.add_column("Type", style="cyan")
    table.add_column("Sentence")
    table.add_row("Original", sentence, style="yellow")
    table.add_row("Split", best_split.replace("\n", " ||"), style="yellow")
    print(table)

    return best_split


def find_split_positions(original: str, modified: str) -> list:
    """找到分割位置

    将 LLM 返回的带 [br] 标记的分割结果映射回原始句子的字符位置
    """
    split_positions = []
    parts = modified.split("[br]")
    start = 0
    language = "zh"
    joiner = get_joiner(language)

    # 清理 parts：去除空白和无效部分
    parts = [p.strip() for p in parts if p.strip()]

    if len(parts) <= 1:
        logger.warning("No valid [br] split markers found in LLM response")
        return []

    for i in range(len(parts) - 1):
        current_part = parts[i]

        # 对于中文，确保当前部分至少包含 3 个字符
        if language == "zh" and len(current_part) < 3:
            logger.warning(f"Part {i + 1} too short ({len(current_part)} chars): '{current_part}', skipping")
            # 将当前部分与下一部分合并，继续查找
            continue

        max_similarity = 0
        best_split = None

        # 在原始句子中查找与当前部分最佳匹配的位置
        for j in range(start + min(3, len(original) - start), len(original)):
            original_left = original[start:j]

            # 对于中文，直接比较字符串
            # 对于英文，需要处理空格
            if language == "zh":
                modified_left = current_part
            else:
                modified_left = joiner.join(current_part.split())

            left_similarity = SequenceMatcher(None, original_left, modified_left).ratio()

            if left_similarity > max_similarity:
                max_similarity = left_similarity
                best_split = j

            # 如果相似度很高，提前结束查找
            if left_similarity >= 0.95:
                break

        # 验证分割点质量
        if max_similarity < 0.7:
            logger.warning(f"Part {i + 1} similarity too low ({max_similarity:.2f}): '{current_part}'")
            continue

        if best_split is not None:
            # 确保分割点不会产生空片段或单字片段
            part_length = best_split - start
            if language == "zh" and part_length < 3:
                logger.warning(f"Split point creates too short part ({part_length} chars), skipping")
                continue
            split_positions.append(best_split)
            start = best_split
        else:
            logger.warning(f"Unable to find split point for part {i + 1}: '{current_part}'")

    return split_positions


if __name__ == "__main__":
    result_zh = [
        "小姐，我们来对我们本章节的内容做一个总结",
        "首先，我们本章节的主题是异步IO和携程本章节，我们引出了携程，",
        "但是到目前为止，我们还没有把携程应用到我们的具体代码当中，这里边",
        "我们的携程一般是需要配合我们的事件循环来使用的",
        "我们携程单独使用的话，实际上它的作用并不是很明显，",
        "而且它使用起来很不方便",
        "关于如何在事件循环中使用携程",
        "我们下一章的SyncIO将会给大家介绍到",
        "我们现在来回顾一下，我们本章节主要的目的是要由浅入深地给大家引出携程它的一个概念",
        "首先，我们来回顾一下本章节的一个主要内容，在最开始的时候，我们介绍了一些概念",
        "这里边包括并发并行同步亦步阻塞和非阻塞这些概念",
        "紧接着我们讲解了C十K问题和IO多路复用",
        "这里边的Io多路复用，包括我们的和易破本节课",
        "给大家详细地讲解了UNIX网络编程中的五种Io模型",
        "以及我们引出了我们的Io多路复用",
        "Io多路复用是我们目前为止使用到的最多的一种技术",
        "我们高并发中使用的Io多路复用的技术非常之多",
        "所以说，我们本章节主要就是围绕着我们的Io多路复用来讲解的",
        "艾欧多洛夫用之后，我们就讲解了如何去使用的",
        "或者说一破加上我们的回调和事件循环的方式去请求我们的U二院",
        "在讲解这种回调和事件循环之前",
        "首先给大家讲解了如何去使用非阻塞的方法",
        "去实现我们的U二元请求",
        "然后我们再引出了我们的回调加事件循环",
        "通过第三章节，我相信大家也体会到了这种编程模式",
        "它和传统的同步L的编程模式差异很大",
        "所以说，我希望大家能够彻底搞清楚，我们这种编程的模式",
        "因为我们异步IO的模型当中",
        "它实际上都是采用了这种模式，包括NodeJS",
        "包括Python中的几乎所有的异步IO的框架",
        "以及我们加瓦里边的内地",
        "它们实际上都是采用这种模式",
        "这里边这个模式，它的核心在于事件循环加上回调",
        "然后我们讲解了回调之痛，",
        "如果我们去采用上面的模式，将它应用到编程当中",
        "实际上我们的编码过程是非常痛苦的",
        "第一个就是站的撕裂的问题",
        "整个调用站如果出现异常就很麻烦",
        "第二个就是嵌套台",
        "这让我们代码维护起来非常的头疼",
        "如果大家写过JS的话，就会知道JS里面有个事件监听",
        "它里边采用的就是回调模式",
        "实际上代码维护起来是很痛苦的",
        "所以说我们后边就引出了携程",
        "携程它本身它并不比我们的事件循环和回调这种编码方式性能高，反而它可能会比这个低一些",
        "但是携程主要解决的问题就是回调之痛的问题",
        "它让我们可以将事件循环加上L多路复用方法和我们的传统的同步编程模式结合起来",
        "携程的主要目的是为了解决整个编码习惯的一个问题",
        "然后我们讲解了生成器里边的剩的克洛斯吃肉以及我们的生成器当中的亚的放",
        "讲解了这些知识，就可以知道实际上可以利用生成器的一些原理来完成将生成器变成我们的携程这么一个过程",
        "这样的话，致辞整个编码",
        "它就可以兼顾我们的事件循环",
        "IO多路复用以及同步编码思维结合起来",
        "然后我们后期再讲解了而Sync和而位置这两个关键词，这两个关键词，它使得最开始，大家注意一下",
        "在而Sync和而位置这两个关键词出现之前，整个携程",
        "它是利用了我们生成器的一些特性，将生成器变成我们的携程",
        "但是有了Sync和Avid之后，整个Python就开始支持我们的原生系统，大家在看以前的一些书籍，或者说以前的一些资料的时候",
        "很多地方都会讲一个装饰器就是coding",
        "它可以将我们的生成器装饰成写成，",
        "但是这里边我强烈建议大家",
        "如果大家使用得出Python的新版本",
        "就不要再去使用以前的克罗汀中式器的模式",
        "尽量的来采用而适应可和而为的这两个关键词",
        "这样的话，我们整个代码的含义是非常明确的，",
        "如果还在使用装饰器，加上生成器来实现我们的携程的话",
        "整个代码的后期维护实际上是会让大家很头疼的",
        "派森既然给我们提供了而适应和就要使用它的原生携程",
        "当然，这里边并没有说明这原生形成它的性能，或者说它其他方面就比我们的生成器这种模式好，它们俩达到的效果都是一样的，但是从语义上来讲",
        "以及从代码的后期维护来讲，是建议大家使用而而而为的",
        "因为我们生成器它实际上还有自己的一个用途",
        "如果大家很想了解这个装饰器背后的原理的话，大家可以进源码看一下，它的内容并不多",
        "实际上是去设置了我们的它的一些等等一些参数的",
        "设置这些参数之后，再去检查我们的一个函数，实际上就可以检查出来，它是不是我们的系统，这个过程实际上并不复杂",
        "在拍摄三点五",
        "三点六以及我们本课程的三点七当中",
        "我都会给大家讲解用而适应和尔维特来实现我们的系统，在前面讲解了那么多",
        "只是为了加深大家对我们携程的一个理解，",
        "因为我如果一上来就讲解而适应和尔维特的话，我相信绝大部分人是听不懂的",
        "本章节，我们关于易波IO和携程就介绍到这里，下一章节",
        "我们将开始来具体通过SyncIO框架来进一步学习我们的携程，好，本章节就到这里，谢谢大家",
    ]
    mean_list = process_meaning_split(result_zh, "zh")
    print(mean_list)
