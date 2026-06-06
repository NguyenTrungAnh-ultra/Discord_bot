import psycopg2
from psycopg2.extras import RealDictCursor
try:
    from pgvector.psycopg2 import register_vector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False
from src.core.db.connection import Database, DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS
from src.utils.date_parser import parse_publish_date

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
    def insert_document(url, title, content, embedding, insight=None, layer=None, entities=None, doc_type=None, ticker=None, publish_date=None, embedded_by='gemini-embedding-2'):
        """
        Inserts a document with its embedding and metadata into the database.
        Includes backward-compatible fallback auto-extraction.
        """
        import json
        
        # 1. Fallback auto-extraction for metadata if not provided
        if not ticker and entities:
            tickers = entities.get('tickers') or entities.get('ticker')
            if isinstance(tickers, list) and tickers:
                ticker = tickers[0]
            elif isinstance(tickers, str):
                ticker = tickers
        
        if not doc_type:
            if entities and entities.get('doc_type'):
                doc_type = entities.get('doc_type')
            elif layer == 'macro':
                doc_type = 'macro'
            elif layer == 'company':
                doc_type = 'company_profile'
                
        if not publish_date:
            raw_date = None
            if entities and isinstance(entities, dict):
                raw_date = entities.get('publish_date') or entities.get('report_date')
            if not raw_date and insight and isinstance(insight, dict):
                raw_date = insight.get('publish_date') or insight.get('report_date')
            
            if raw_date:
                publish_date = parse_publish_date(raw_date)
        else:
            publish_date = parse_publish_date(publish_date)

        insight_json = json.dumps(insight) if insight else None
        entities_json = json.dumps(entities) if entities else None
        
        if not HAS_PGVECTOR:
            print("Skipping DB insertion as pgvector is not available.")
            return

        query = """
        INSERT INTO research_documents (url, title, content, embedding, insight, layer, entities, doc_type, ticker, publish_date, embedded_by)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (url) DO UPDATE SET
            title = EXCLUDED.title,
            content = EXCLUDED.content,
            embedding = EXCLUDED.embedding,
            insight = EXCLUDED.insight,
            layer = EXCLUDED.layer,
            entities = EXCLUDED.entities,
            doc_type = EXCLUDED.doc_type,
            ticker = EXCLUDED.ticker,
            publish_date = EXCLUDED.publish_date,
            embedded_by = EXCLUDED.embedded_by;
        """
        try:
            VectorDatabase.execute_query(query, (
                url, title, content, embedding, insight_json, 
                layer, entities_json, doc_type, ticker, publish_date, embedded_by
            ))
        except Exception as e:
            print(f"Failed to insert document: {e}")

    @staticmethod
    def get_document_by_url(url: str):
        """Retrieves a document by its URL."""
        query = "SELECT insight, layer, entities, doc_type, ticker, publish_date, embedded_by FROM research_documents WHERE url = %s"
        results = VectorDatabase.execute_query(query, (url,), fetch=True)
        return results[0] if results else None


    @staticmethod
    def search_with_filters(query_embedding, ticker=None, doc_type=None, start_date=None, end_date=None, limit=5, min_similarity=0.3):
        """
        Searches similar documents with additional filters (ticker, doc_type, date range, and similarity threshold).
        Uses a clean nested subquery to handle dynamic filters properly.
        """
        if not HAS_PGVECTOR:
            print("pgvector not available, returning empty search results.")
            return []

        conditions = []
        params = []

        if ticker:
            conditions.append("ticker = %s")
            params.append(ticker)
        if doc_type:
            conditions.append("doc_type = %s")
            params.append(doc_type)
        if start_date:
            parsed_start = parse_publish_date(start_date)
            if parsed_start:
                conditions.append("publish_date >= %s")
                params.append(parsed_start)
        if end_date:
            parsed_end = parse_publish_date(end_date)
            if parsed_end:
                conditions.append("publish_date <= %s")
                params.append(parsed_end)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # SQL subquery:
        # 1. Calculates cosine similarity
        # 2. Filters by the dynamic conditions
        # 3. Outer query filters by min_similarity and orders by highest similarity
        sql = f"""
        SELECT * FROM (
            SELECT id, url, title, content, insight, layer, entities, doc_type, ticker, publish_date, 
                   1 - (embedding <=> %s::vector) AS similarity
            FROM research_documents
            {where_clause}
        ) sub
        WHERE similarity >= %s
        ORDER BY similarity DESC
        LIMIT %s;
        """
        
        # Build query parameters list:
        # First parameter: query_embedding (used in outer calculations)
        # Then all WHERE conditions
        # Then min_similarity
        # Then limit
        full_params = [query_embedding] + params + [min_similarity, limit]
        
        return VectorDatabase.execute_query(sql, tuple(full_params), fetch=True)

    @staticmethod
    def search_by_metadata(ticker=None, doc_type=None, limit=5):
        """
        Retrieves documents filtering solely by metadata, ordered by publish date desc.
        Useful for metadata-only fallback lookups.
        """
        conditions = []
        params = []
        if ticker:
            conditions.append("ticker = %s")
            params.append(ticker)
        if doc_type:
            conditions.append("doc_type = %s")
            params.append(doc_type)
            
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
            
        sql = f"""
        SELECT id, url, title, content, insight, layer, entities, doc_type, ticker, publish_date, created_at
        FROM research_documents
        {where_clause}
        ORDER BY publish_date DESC, created_at DESC
        LIMIT %s;
        """
        params.append(limit)
        return VectorDatabase.execute_query(sql, tuple(params), fetch=True)

