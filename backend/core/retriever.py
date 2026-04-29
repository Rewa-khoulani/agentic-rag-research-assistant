from sentence_transformers import SentenceTransformer
import chromadb
import cohere
from config import CHROMA_PERSIST_DIR, COLLECTION_NAME, EMBEDDING_MODEL_NAME, COHERE_API_KEY
import os

class Retriever:
    def __init__(self):
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        self.chroma_client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
        self.co_client = cohere.Client(COHERE_API_KEY or os.getenv("COHERE_API_KEY"))
        self.collection = None

    def create_collection(self, chunks, collection_name=COLLECTION_NAME):
        try:
            self.chroma_client.delete_collection(collection_name)
        except:
            pass
        self.collection = self.chroma_client.create_collection(collection_name)

        ids = []
        documents = []
        embeddings = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            ids.append(str(i))
            documents.append(chunk["text"])
            embeddings.append(self.embedding_model.encode(chunk["text"]).tolist())
            metadatas.append({
                "page": str(chunk.get("page", "N/A")),
                "section": chunk.get("section", "General")
            })

        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )
        return self.collection

    def load_collection(self, collection_name=COLLECTION_NAME):
        self.collection = self.chroma_client.get_collection(collection_name)
        return self.collection

    def retrieve(self, query, top_k=15, section_filter=None, page_filter=None):
        query_embedding = self.embedding_model.encode(query).tolist()
        where_filter = {}
        if section_filter:
            where_filter["section"] = section_filter
        if page_filter is not None:
            where_filter["page"] = str(page_filter)
        if not where_filter:
            where_filter = None
        print(f"\n🔎 [retrieve] query='{query[:80]}...', section_filter='{section_filter}', page_filter='{page_filter}', where={where_filter}")

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter
        )
        if results["documents"] and results["documents"][0]:
            for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
                print(f"   → قطعة {i+1}: page={meta.get('page', '?')}, section='{meta.get('section', '?')}'")
        else:
            print("   ⚠️ لا توجد نتائج.")
        return results
    def rerank(self, query, initial_results, top_k=5):
        if not initial_results["documents"] or not initial_results["documents"][0]:
            return []
        docs = initial_results["documents"][0]
        metadatas = initial_results["metadatas"][0]
    
        print(f"\n🔁 [Rerank] جاري إعادة ترتيب {len(docs)} قطعة باستخدام Cohere...")
        response = self.co_client.rerank(
            model="rerank-english-v3.0",
            query=query,
            documents=docs,
          top_n=top_k
        )
        final_results = []
        for res in response.results:
            idx = res.index
            meta = metadatas[idx]
            section = meta.get("section", "?")
            page = meta.get("page", "?")
            snippet = docs[idx][:100].replace('\n', ' ')
            print(f"   🎯 المرتبة {len(final_results)+1}: score={res.relevance_score:.4f}, page={page}, section='{section}' | {snippet}...")
            final_results.append({
             "text": docs[idx], 
                "metadata": meta,
                "score": res.relevance_score
            })
    
        print(f"✅ [Rerank] اكتملت إعادة الترتيب، أفضل {len(final_results)} نتيجة\n")
        return final_results
    # def rerank(self, query, initial_results, top_k=5):
    #     if not initial_results["documents"] or not initial_results["documents"][0]:
    #         return []
    #     docs = initial_results["documents"][0]
    #     metadatas = initial_results["metadatas"][0]
    #     response = self.co_client.rerank(
    #         model="rerank-english-v3.0",
    #         query=query,
    #         documents=docs,
    #         top_n=top_k
    #     )
    #     final_results = []
    #     for res in response.results:
    #         idx = res.index
    #         final_results.append({
    #             "text": docs[idx],
    #             "metadata": metadatas[idx],
    #             "score": res.relevance_score
    #         })
    #     return final_results
    # def rerank(self, query, initial_results, top_k=5):
    # # إذا لم تكن هناك نتائج، أرجع قائمة فارغة
    #     if not initial_results["documents"] or not initial_results["documents"][0]:
    #         return []
    
    # # بدلاً من استدعاء Cohere، نأخذ أول top_k من النتائج الأولية
    #     docs = initial_results["documents"][0]
    #     metadatas = initial_results["metadatas"][0]
    
    #     final_results = []
    #     for i in range(min(top_k, len(docs))):
    #         final_results.append({
    #             "text": docs[i],
    #             "metadata": metadatas[i],
    #             "score": 1.0  # قيمة افتراضية
    #      })
    #     return final_results
    def get_available_sections(self):
        from backend.utils import get_available_sections
        return get_available_sections(self.collection)

    def get_available_pages(self):
        from backend.utils import get_available_pages
        return get_available_pages(self.collection)

retriever = Retriever()