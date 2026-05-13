import psycopg2
from psycopg2.extras import RealDictCursor
try:
    from pgvector.psycopg2 import register_vector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False
from src.core.db import Database, DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS

class VectorDatabase(Database):
    """Database helper with pgvector support."""
    
    @staticmethod
    def get_connection():
        """Returns a new connection with pgvector registered if available."""
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        if HAS_PGVECTOR:
            try:
                register_vector(conn)
            except Exception as e:
                print(f"Warning: Could not register pgvector: {e}")
        return conn

    @staticmethod
    def execute_query(query, params=None, fetch=False):
        """Executes a query with pgvector support."""
        conn = VectorDatabase.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                if fetch:
                    return cur.fetchall()
                conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Vector Database error: {e}")
            raise e
        finally:
            conn.close()

    @staticmethod
    def insert_document(url, title, content, embedding, insight=None, layer=None, entities=None):
        """Inserts a document with its embedding and metadata into the database."""
        import json
        insight_json = json.dumps(insight) if insight else None
        entities_json = json.dumps(entities) if entities else None
        
        if not HAS_PGVECTOR:
            print("Skipping DB insertion as pgvector is not available.")
            return

        query = """
        INSERT INTO research_documents (url, title, content, embedding, insight, layer, entities)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (url) DO UPDATE SET
            title = EXCLUDED.title,
            content = EXCLUDED.content,
            embedding = EXCLUDED.embedding,
            insight = EXCLUDED.insight,
            layer = EXCLUDED.layer,
            entities = EXCLUDED.entities;
        """
        try:
            VectorDatabase.execute_query(query, (url, title, content, embedding, insight_json, layer, entities_json))
        except Exception as e:
            print(f"Failed to insert document: {e}")

    @staticmethod
    def get_document_by_url(url: str):
        """Retrieves a document by its URL."""
        query = "SELECT insight FROM research_documents WHERE url = %s"
        results = VectorDatabase.execute_query(query, (url,), fetch=True)
        return results[0] if results else None

    @staticmethod
    def search_similar(query_embedding, limit=5):
        """Searches for similar documents using cosine similarity."""
        if not HAS_PGVECTOR:
            print("pgvector not available, returning empty search results.")
            return []
            
        query = """
        SELECT url, title, content, insight, 1 - (embedding <=> %s) AS similarity
        FROM research_documents
        ORDER BY embedding <=> %s
        LIMIT %s;
        """
        return VectorDatabase.execute_query(query, (query_embedding, query_embedding, limit), fetch=True)
