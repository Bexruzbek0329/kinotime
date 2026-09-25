"""Add content_type, total_seasons, total_episodes columns to movies table."""
import asyncio
from sqlalchemy import text
from database.engine import engine

async def migrate():
    async with engine.begin() as conn:
        # Create enum type if not exists
        await conn.execute(text("""
            DO $$ BEGIN
                CREATE TYPE contenttype AS ENUM ('movie', 'serial');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))
        
        # Add content_type column if not exists
        await conn.execute(text("""
            ALTER TABLE movies 
            ADD COLUMN IF NOT EXISTS content_type contenttype DEFAULT 'movie' NOT NULL;
        """))
        
        # Add total_seasons column if not exists
        await conn.execute(text("""
            ALTER TABLE movies 
            ADD COLUMN IF NOT EXISTS total_seasons INTEGER;
        """))
        
        # Add total_episodes column if not exists
        await conn.execute(text("""
            ALTER TABLE movies 
            ADD COLUMN IF NOT EXISTS total_episodes INTEGER;
        """))
        
        # Create index on content_type if not exists
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_movies_content_type ON movies(content_type);
        """))
        
        print("[✓] Migration completed successfully!")

if __name__ == "__main__":
    asyncio.run(migrate())
