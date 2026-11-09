from sentence_transformers import SentenceTransformer
import chromadb
import cohere
from config import CHROMA_PERSIST_DIR, COLLECTION_NAME, EMBEDDING_MODEL_NAME, COHERE_API_KEY
import os
from rank_bm25 import BM25Okapi
import hashlib
import time
class Retriever:
    # def __init__(self):
        # self.embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        # self.chroma_client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
        # self.co_client = cohere.Client(COHERE_API_KEY or os.getenv("COHERE_API_KEY"))
        # self.collection = None
        # self.documents_corpus = []   # نصوص كل القطع (بدون section_label)
        # self.bm25_index = None
    def __init__(self):
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

        self.chroma_client = chromadb.PersistentClient(
            path=str(CHROMA_PERSIST_DIR)
        )

        self.co_client = cohere.Client(
            COHERE_API_KEY or os.getenv("COHERE_API_KEY")
        )

        try:
            self.collection = self.chroma_client.get_collection(COLLECTION_NAME)
            print(f"✅ Loaded collection: {COLLECTION_NAME}")

        except Exception as e:
            print(f"⚠️ Collection not found yet: {e}")
            self.collection = None

        self.documents_corpus = []
        self.bm25_index = None

    
    def create_collection(self, chunks, collection_name=None):
        # دائماً ولّدي اسماً فريداً (تجاهلي ما يمرره app.py)
        collection_name = f"papers_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"
        print(f"📦 Creating collection: {collection_name}")
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
            if not chunk["text"].strip():
                print(f"⚠️ تحذير: قطعة {i} فارغة، سيتم تجاهلها.")
                continue
            ids.append(str(i))
            documents.append(chunk["text"])
            embeddings.append(self.embedding_model.encode(chunk["text"]).tolist())
            # metadatas.append({
            #     "page": str(chunk.get("page", "N/A")),
            #     "section": chunk.get("section", "General"),
            #      "chunk_id": i
                
            # })
            metadatas.append({
                "page": str(chunk.get("page", "N/A")),
                "section": chunk.get("section", "General"),
                "chunk_id": i,
                "doc_type": "chunk"
            })

        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

        # --- إضافة أسماء الأقسام كوثائق منفصلة للبحث التلقائي ---
        section_names = list(set(
            c["section"] for c in chunks 
            if c.get("section") and c["section"] != "General"
        ))
        if section_names:
            section_embeddings = self.embedding_model.encode(section_names)
            section_ids = [f"section_{i}" for i in range(len(section_names))]
            section_metadatas = [{"doc_type": "section_label", "section": s} for s in section_names]
            if not embeddings:
                 raise ValueError("لم يتم توليد أي تضمينات. تحقق من النصوص المستخرجة.")
            self.collection.add(
                ids=section_ids,
                documents=section_names,
                embeddings=section_embeddings.tolist(),
                metadatas=section_metadatas
            )
            print(f"🏷️ تم تخزين {len(section_names)} أقسام كعلامات للبحث التلقائي.")
            # --- بناء فهرس BM25 (للقطع الحقيقية فقط) ---
        all_data = self.collection.get(where={"doc_type": {"$ne": "section_label"}})
        if all_data["documents"]:
            tokenized = [doc.split() for doc in all_data["documents"]]
            self.bm25_index = BM25Okapi(tokenized)
            self.documents_corpus = all_data["documents"]
        return self.collection
    # def create_collection(self, chunks, collection_name=COLLECTION_NAME):
    #     try:
    #         self.chroma_client.delete_collection(collection_name)
    #     except:
    #         pass
    #     self.collection = self.chroma_client.create_collection(collection_name)

    #     ids = []
    #     documents = []
    #     embeddings = []
    #     metadatas = []

    #     for i, chunk in enumerate(chunks):
    #         ids.append(str(i))
    #         documents.append(chunk["text"])
    #         embeddings.append(self.embedding_model.encode(chunk["text"]).tolist())
    #         metadatas.append({
    #             "page": str(chunk.get("page", "N/A")),
    #             "section": chunk.get("section", "General")
    #         })

    #     self.collection.add(
    #         ids=ids,
    #         documents=documents,
    #         embeddings=embeddings,
    #         metadatas=metadatas
    #     )
    #     return self.collection
    def bm25_search(self, query: str, top_k: int = 15):
        if not self.bm25_index:
            return []
        tokenized_query = query.split()
        scores = self.bm25_index.get_scores(tokenized_query)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [(self.documents_corpus[i], scores[i]) for i in top_indices]
    
    def load_collection(self, collection_name=COLLECTION_NAME):
        self.collection = self.chroma_client.get_collection(collection_name)
        return self.collection

    def retrieve(self, query, top_k=15, section_filter=None, page_filter=None, where_filter1=None):
        query_embedding = self.embedding_model.encode(query).tolist()
        
        where_filter = {}
        if section_filter:
            where_filter["section"] = section_filter
        if page_filter is not None:
            where_filter["page"] = str(page_filter)
        if where_filter1:
            where_filter.update(where_filter1)
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
                print(f"   →  {i+1}:  section='{meta.get('section', '?')}'")
        else:
            print("   ⚠️ لا توجد نتائج.")
        return results
    def rerank(self, query, initial_results, top_k=5,score_threshold=0.70):
        if not initial_results["documents"] or not initial_results["documents"][0]:
            return []
        docs = initial_results["documents"][0]
        metadatas = initial_results["metadatas"][0]
    
        print(f"\n🔁 [Rerank] {len(docs)}  with Cohere...")
        response = self.co_client.rerank(
            model="rerank-english-v3.0",
            query=query,
            documents=docs,
        #   top_n=top_k
            top_n=len(docs)
        )
        final_results = []
        for res in response.results:
            idx = res.index
            score = res.relevance_score
            if score_threshold is not None and score < score_threshold:
                continue
            # meta = metadatas[idx]
            # section = meta.get("section", "?")
            # page = meta.get("page", "?")
            snippet = docs[idx][:100].replace('\n', ' ')
            print(f"   🎯 score={score:.4f}, page={metadatas[idx].get('page', '?')}, section='{metadatas[idx].get('section', '?')}' | {snippet}...")
            # print(f"   🎯 المرتبة {len(final_results)+1}: score={res.relevance_score:.4f}, page={page}, section='{section}' | {snippet}...")
            # final_results.append({
            #  "text": docs[idx], 
            #     "metadata": meta,
            #     "score": res.relevance_score
            # })
          
            final_results.append({
                "text": docs[idx],
                "metadata": metadatas[idx],
                "score": score
            })
    
        print(f"✅ [Rerank]   completle rerank {len(final_results)} result\n")
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




