"""
ChromaDB Cleanup Utility - Remove Orphaned Documents

This script helps clean up the ChromaDB vector store by:
1. Identifying documents whose source files no longer exist
2. Removing duplicate documents
3. Providing detailed cleanup report

Usage:
    python scripts/cleanup_vectorstore.py [--dry-run]
"""
import sys
import os
import logging
from pathlib import Path
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.storage.vector_store import VectorStore
from app.config import settings

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def analyze_vector_store():
    """Analyze vector store for issues"""
    logger.info("=" * 70)
    logger.info("CHROMADB ANALYSIS UTILITY")
    logger.info("=" * 70)
    
    vector_store = VectorStore()
    
    # Get all documents
    all_docs = vector_store.chroma_client.get_documents()
    
    if not all_docs or 'metadatas' not in all_docs or 'ids' not in all_docs:
        logger.info("✓ Vector store is empty")
        return
    
    total_docs = len(all_docs['ids'])
    logger.info(f"\n[STATS] Total documents in vector store: {total_docs}")
    logger.info(f"[STATS] Collection: {settings.collection_name}")
    
    # Analyze by source file
    source_files = defaultdict(list)
    modality_counts = defaultdict(int)
    orphaned_docs = []
    missing_source_docs = []
    
    for doc_id, metadata in zip(all_docs['ids'], all_docs['metadatas']):
        source_file = metadata.get('source_file', None)
        modality = metadata.get('modality', 'unknown')
        
        modality_counts[modality] += 1
        
        if not source_file:
            missing_source_docs.append(doc_id)
            continue
        
        source_files[source_file].append({
            'id': doc_id,
            'modality': modality,
            'metadata': metadata
        })
        
        # Check if file exists
        if not Path(source_file).exists():
            orphaned_docs.append({
                'id': doc_id,
                'source': source_file,
                'modality': modality
            })
    
    # Report findings
    logger.info(f"\n[STATS] Documents by modality:")
    for modality, count in sorted(modality_counts.items()):
        logger.info(f"   {modality}: {count}")
    
    logger.info(f"\n[STATS] Unique source files: {len(source_files)}")
    
    # Report duplicates
    logger.info(f"\n[CHECK] Checking for duplicates...")
    duplicates = {source: docs for source, docs in source_files.items() if len(docs) > 20}
    if duplicates:
        logger.warning(f"\n[WARN] Found {len(duplicates)} files with >20 chunks (potential duplicates):")
        for source, docs in sorted(duplicates.items(), key=lambda x: -len(x[1]))[:10]:
            exists = "✓" if Path(source).exists() else "✗"
            logger.warning(f"   {exists} {Path(source).name}: {len(docs)} chunks")
    else:
        logger.info("   ✓ No obvious duplicates found")
    
    # Report orphaned documents
    if orphaned_docs:
        logger.warning(f"\n[WARN] Found {len(orphaned_docs)} orphaned documents (files deleted from disk):")
        orphaned_by_source = defaultdict(list)
        for doc in orphaned_docs:
            orphaned_by_source[doc['source']].append(doc['id'])
        
        for source, ids in sorted(orphaned_by_source.items())[:10]:
            logger.warning(f"   [X] {Path(source).name}: {len(ids)} chunks")
        
        if len(orphaned_by_source) > 10:
            logger.warning(f"   ... and {len(orphaned_by_source) - 10} more files")
    else:
        logger.info("\n[OK] No orphaned documents found")
    
    if missing_source_docs:
        logger.warning(f"\n[WARN] Found {len(missing_source_docs)} documents with missing source_file metadata")
    
    return {
        'total_docs': total_docs,
        'orphaned_docs': orphaned_docs,
        'missing_source_docs': missing_source_docs,
        'duplicates': duplicates
    }


def cleanup_orphaned_documents(dry_run=True):
    """Clean up orphaned documents"""
    logger.info("\n" + "=" * 70)
    if dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
    else:
        logger.info("CLEANUP MODE - Removing orphaned documents")
    logger.info("=" * 70)
    
    vector_store = VectorStore()
    all_docs = vector_store.chroma_client.get_documents()
    
    if not all_docs or 'metadatas' not in all_docs or 'ids' not in all_docs:
        logger.info("✓ Nothing to clean up")
        return
    
    # Find orphaned documents
    orphaned_ids = []
    orphaned_sources = set()
    
    for doc_id, metadata in zip(all_docs['ids'], all_docs['metadatas']):
        source_file = metadata.get('source_file', '')
        
        if not source_file or not Path(source_file).exists():
            orphaned_ids.append(doc_id)
            orphaned_sources.add(source_file if source_file else '<missing>')
    
    if not orphaned_ids:
        logger.info("\n[OK] No orphaned documents to clean up")
        return
    
    logger.info(f"\n[CLEANUP] Found {len(orphaned_ids)} orphaned documents from {len(orphaned_sources)} sources")
    
    if dry_run:
        logger.info("\nWould delete documents from:")
        for source in sorted(orphaned_sources)[:20]:
            logger.info(f"   [X] {Path(source).name if source != '<missing>' else '<missing source>'}")
        if len(orphaned_sources) > 20:
            logger.info(f"   ... and {len(orphaned_sources) - 20} more")
    else:
        logger.info("\n[DELETE] Deleting orphaned documents...")
        vector_store.chroma_client.delete_documents(ids=orphaned_ids)
        logger.info(f"[SUCCESS] Deleted {len(orphaned_ids)} orphaned documents")
        
        # Verify
        remaining = vector_store.chroma_client.get_document_count()
        logger.info(f"[STATS] Remaining documents: {remaining}")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean up ChromaDB vector store')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be deleted without actually deleting')
    parser.add_argument('--clean', action='store_true',
                       help='Actually perform cleanup (removes orphaned documents)')
    
    args = parser.parse_args()
    
    # Always analyze first
    analysis = analyze_vector_store()
    
    # Cleanup if requested
    if args.clean or args.dry_run:
        cleanup_orphaned_documents(dry_run=args.dry_run)
    else:
        logger.info("\n💡 Tip: Use --dry-run to see what would be deleted")
        logger.info("💡 Use --clean to actually remove orphaned documents")
    
    logger.info("\n" + "=" * 70)
    logger.info("Analysis complete!")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
