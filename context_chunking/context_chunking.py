from kiwipiepy import Kiwi
from sentence_transformers import SentenceTransformer

def split_kiwi(file_path):

    kiwi=Kiwi()
    file=open(file_path,'r')
    x=file.read()
    temp=kiwi.split_into_sents(x)

    sentences=[]
    for idx in range(len(temp)):
        sentences.append(temp[idx].text)
    return sentences

def sentence_embed(sentences,model_name='intfloat/multilingual-e5-large-instruct'):
    model=SentenceTransformer(model_name)
    embeddings = model.encode(sentences, convert_to_tensor=True)

    return embeddings

def chunk_sentences(sentences,embeddings,similarity_threshold=0.8,model_name='intfloat/multilingual-e5-large-instruct',max_chunk_size=5):
    model=SentenceTransformer(model_name)
    chunks=[]
    current_chunk=[sentences[0]]
    for i in range(1, len(sentences)):
        similarity = model.similarity(embeddings[i - 1], embeddings[i]).item()
        
        if similarity < similarity_threshold or len(current_chunk) >= max_chunk_size:
            chunks.append(current_chunk)
            current_chunk = [sentences[i]]
        else:
            current_chunk.append(sentences[i])

    # 마지막 청크 추가
    if current_chunk:
        chunks.append(current_chunk)

    return chunks


file_path = 'data/processed/stt_result_1_processed.txt'
sentences = split_kiwi(file_path)
embeddings = sentence_embed(sentences)

# 청킹 실행
chunks = chunk_sentences(sentences, embeddings, similarity_threshold=0.7, max_chunk_size=10)

# 결과 출력
for idx, chunk in enumerate(chunks, 1):
    print(f"Chunk {idx}:")
    for sentence in chunk:
        print(sentence,end=' ')
    print()