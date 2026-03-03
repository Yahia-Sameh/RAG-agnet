import fitz  # PyMuPDF
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.app.config import config

class SimpleContractQA:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=config.GEMINI_MODEL,
            google_api_key=config.GEMINI_API_KEY,
            temperature=0.1
        )
        self.pages = []  # List of (page_num, text)
        self.filename = ""
    
    def load_pdf(self, file_path):
        """Load PDF and store pages"""
        doc = fitz.open(file_path)
        self.pages = []
        self.filename = file_path.split("/")[-1]
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                self.pages.append((page_num + 1, text))
        
        doc.close()
        return {
            "pages": len(self.pages),
            "filename": self.filename,
            "status": "loaded"
        }
    
    def keyword_search(self, question, top_k=3):
        """Simple keyword search - finds pages containing question keywords"""
        # Extract keywords (words longer than 3 chars, excluding common words)
        common_words = {'what', 'is', 'the', 'in', 'of', 'to', 'and', 'a', 'for', 
                       'on', 'with', 'this', 'that', 'does', 'can', 'are', 'tell', 'me'}
        words = question.lower().split()
        keywords = [w for w in words if w not in common_words and len(w) > 2]
        
        if not keywords:
            keywords = words[:3]  # Take first 3 words if no good keywords
        
        # Score each page
        scored_pages = []
        for page_num, text in self.pages:
            text_lower = text.lower()
            score = 0
            matched = []
            
            for kw in keywords:
                if kw in text_lower:
                    score += 1
                    matched.append(kw)
            
            if score > 0:
                scored_pages.append({
                    "page": page_num,
                    "score": score,
                    "text": text[:1500],  # First 1500 chars
                    "keywords": matched
                })
        
        # Sort by score
        scored_pages.sort(key=lambda x: x["score"], reverse=True)
        return scored_pages[:top_k]
    
    def ask(self, question):
        """Answer question using keyword search + Gemini"""
        if not self.pages:
            return {"answer": "Please upload a PDF first.", "sources": []}
        
        # Find relevant pages
        relevant_pages = self.keyword_search(question)
        
        if not relevant_pages:
            # Fallback to first 2 pages
            context_pages = self.pages[:2]
            context = ""
            sources = []
            for page_num, text in context_pages:
                context += f"\n[Page {page_num}]\n{text[:1500]}\n"
                sources.append({"page": page_num, "text": text[:150] + "..."})
        else:
            context = ""
            sources = []
            for p in relevant_pages:
                context += f"\n[Page {p['page']}]\n{p['text']}\n"
                sources.append({
                    "page": p["page"],
                    "text": p["text"][:150] + "..."
                })
        
        prompt = f"""You are a contract assistant. Answer based ONLY on these document pages.

DOCUMENT PAGES:
{context}

QUESTION: {question}

INSTRUCTIONS:
1. Answer ONLY using information from the pages above
2. If answer isn't there, say "I cannot find this information"
3. Be concise and specific

ANSWER:"""
        
        response = self.llm.invoke(prompt)
        
        return {
            "answer": response.content,
            "sources": sources
        }
    
    def get_summary(self):
        """Generate document summary"""
        if not self.pages:
            return "No document loaded"
        
        # Use first 2 pages and last page for summary
        summary_pages = []
        if len(self.pages) >= 3:
            summary_pages = [self.pages[0], self.pages[1], self.pages[-1]]
        else:
            summary_pages = self.pages
        
        context = ""
        for page_num, text in summary_pages:
            context += f"\n[Page {page_num}]\n{text[:1000]}\n"
        
        prompt = f"""Summarize this contract in 3-4 sentences.
Focus on: parties, purpose, key terms, dates.

DOCUMENT:
{context}

SUMMARY:"""
        
        response = self.llm.invoke(prompt)
        return response.content
