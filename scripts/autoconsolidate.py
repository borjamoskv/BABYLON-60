import asyncio
from babylon60.database.core import connect
from babylon60.memory.journal import JournalEntry

async def autoconsolidate(batch_size: int = 500) -> None:
    async with connect() as db:
        cursor = await db.execute('SELECT id FROM journal ORDER BY lamport_t')
        rows = await cursor.fetchall()
        ids = [row[0] for row in rows]
        for i in range(0, len(ids), batch_size):
            batch = ids[i:i+batch_size]
            entries = [await JournalEntry.load(id) for id in batch]
            merged = JournalEntry.merge(entries)
            await merged.save()
            # Delete old entries, respecting INV_BFT_04 semantics
            placeholders = ','.join('?' for _ in batch)
            await db.execute(f'DELETE FROM journal WHERE id IN ({placeholders})', tuple(batch))
        await db.commit()

if __name__ == '__main__':
    asyncio.run(autoconsolidate())
