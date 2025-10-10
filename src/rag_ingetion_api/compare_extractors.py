"""
Document Extraction Comparison Tool

This tool compares document extraction using:
1. Unstructured library
2. AzureAIDocumentIntelligenceLoader (LangChain)

It processes all documents in a specified folder and generates a detailed comparison report.
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import argparse
from dotenv import load_dotenv


@dataclass
class ExtractionResult:
    """Results from a single document extraction"""
    filename: str
    file_size_bytes: int
    extractor: str  # "unstructured" or "azure_di"
    success: bool
    extraction_time_seconds: float
    text_length: int
    chunk_count: Optional[int] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    warnings: Optional[List[str]] = None


@dataclass
class ComparisonReport:
    """Comprehensive comparison report"""
    timestamp: str
    total_files: int
    unstructured_results: List[ExtractionResult]
    azure_di_results: List[ExtractionResult]
    summary: Dict[str, Any]


class UnstructuredExtractor:
    """Wrapper for Unstructured library extraction"""

    def __init__(self):
        try:
            from unstructured.partition.auto import partition
            from unstructured.cleaners.core import clean_extra_whitespace
            self.partition = partition
            self.clean_extra_whitespace = clean_extra_whitespace
            self.available = True
        except ImportError as e:
            self.available = False
            self.import_error = str(e)

    def extract(self, file_path: str) -> ExtractionResult:
        """Extract text from document using Unstructured"""
        start_time = time.time()
        file_size = os.path.getsize(file_path)
        filename = os.path.basename(file_path)

        if not self.available:
            return ExtractionResult(
                filename=filename,
                file_size_bytes=file_size,
                extractor="unstructured",
                success=False,
                extraction_time_seconds=0.0,
                text_length=0,
                error=f"Unstructured library not available: {self.import_error}"
            )

        try:
            # Partition the document
            elements = self.partition(filename=file_path)

            # Clean and concatenate text
            text_parts = []
            for element in elements:
                text = str(element)
                # Apply cleaning
                cleaned_text = self.clean_extra_whitespace(text)
                text_parts.append(cleaned_text)

            full_text = "\n".join(text_parts)
            extraction_time = time.time() - start_time

            # Extract metadata if available
            metadata = {}
            if elements and hasattr(elements[0], 'metadata'):
                metadata = {
                    "element_count": len(elements),
                    "element_types": list(set([type(el).__name__ for el in elements]))
                }

            return ExtractionResult(
                filename=filename,
                file_size_bytes=file_size,
                extractor="unstructured",
                success=True,
                extraction_time_seconds=extraction_time,
                text_length=len(full_text),
                chunk_count=len(elements),
                metadata=metadata
            )

        except Exception as e:
            extraction_time = time.time() - start_time
            return ExtractionResult(
                filename=filename,
                file_size_bytes=file_size,
                extractor="unstructured",
                success=False,
                extraction_time_seconds=extraction_time,
                text_length=0,
                error=str(e)
            )


class AzureDocumentIntelligenceExtractor:
    """Wrapper for Azure AI Document Intelligence extraction"""

    def __init__(self, endpoint: Optional[str] = None, api_key: Optional[str] = None):
        self.endpoint = endpoint or os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        self.api_key = api_key or os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY")

        try:
            from langchain_community.document_loaders import AzureAIDocumentIntelligenceLoader
            self.AzureAIDocumentIntelligenceLoader = AzureAIDocumentIntelligenceLoader
            self.available = True if (self.endpoint and self.api_key) else False
            self.import_error = None if self.available else "Missing AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT or AZURE_DOCUMENT_INTELLIGENCE_KEY"
        except ImportError as e:
            self.available = False
            self.import_error = str(e)

    def extract(self, file_path: str) -> ExtractionResult:
        """Extract text from document using Azure Document Intelligence"""
        start_time = time.time()
        file_size = os.path.getsize(file_path)
        filename = os.path.basename(file_path)

        if not self.available:
            return ExtractionResult(
                filename=filename,
                file_size_bytes=file_size,
                extractor="azure_di",
                success=False,
                extraction_time_seconds=0.0,
                text_length=0,
                error=f"Azure DI not available: {self.import_error}"
            )

        try:
            # Load document with Azure DI
            loader = self.AzureAIDocumentIntelligenceLoader(
                api_endpoint=self.endpoint,
                api_key=self.api_key,
                file_path=file_path,
                api_model="prebuilt-layout",  # Use layout model for best extraction
                mode="markdown"  # Output as markdown for better structure
            )

            documents = loader.load()

            # Concatenate all document pages
            full_text = "\n\n".join([doc.page_content for doc in documents])
            extraction_time = time.time() - start_time

            # Extract metadata
            metadata = {}
            if documents:
                metadata = {
                    "page_count": len(documents),
                    "metadata_keys": list(documents[0].metadata.keys()) if documents[0].metadata else []
                }

            return ExtractionResult(
                filename=filename,
                file_size_bytes=file_size,
                extractor="azure_di",
                success=True,
                extraction_time_seconds=extraction_time,
                text_length=len(full_text),
                chunk_count=len(documents),
                metadata=metadata
            )

        except Exception as e:
            extraction_time = time.time() - start_time
            return ExtractionResult(
                filename=filename,
                file_size_bytes=file_size,
                extractor="azure_di",
                success=False,
                extraction_time_seconds=extraction_time,
                text_length=0,
                error=str(e)
            )


class DocumentExtractionComparator:
    """Main comparison tool"""

    def __init__(self, azure_endpoint: Optional[str] = None, azure_key: Optional[str] = None):
        self.unstructured = UnstructuredExtractor()
        self.azure_di = AzureDocumentIntelligenceExtractor(azure_endpoint, azure_key)

    def compare_folder(self, folder_path: str, supported_extensions: List[str] = None) -> ComparisonReport:
        """Compare extraction on all documents in a folder"""

        if supported_extensions is None:
            supported_extensions = ['.pdf', '.docx', '.doc', '.pptx', '.txt', '.html', '.md']

        folder = Path(folder_path)
        if not folder.exists() or not folder.is_dir():
            raise ValueError(f"Folder not found: {folder_path}")

        # Find all supported documents
        files = []
        for ext in supported_extensions:
            files.extend(folder.glob(f"**/*{ext}"))

        if not files:
            raise ValueError(f"No supported documents found in {folder_path}")

        print(f"\n{'='*80}")
        print(f"Document Extraction Comparison")
        print(f"{'='*80}")
        print(f"Folder: {folder_path}")
        print(f"Files found: {len(files)}")
        print(f"{'='*80}\n")

        unstructured_results = []
        azure_di_results = []

        for i, file_path in enumerate(files, 1):
            print(f"[{i}/{len(files)}] Processing: {file_path.name}")

            # Extract with Unstructured
            print(f"  → Unstructured...", end=" ")
            unstruct_result = self.unstructured.extract(str(file_path))
            unstructured_results.append(unstruct_result)
            status = "✓" if unstruct_result.success else "✗"
            print(f"{status} ({unstruct_result.extraction_time_seconds:.2f}s)")

            # Extract with Azure DI
            print(f"  → Azure DI...", end=" ")
            azure_result = self.azure_di.extract(str(file_path))
            azure_di_results.append(azure_result)
            status = "✓" if azure_result.success else "✗"
            print(f"{status} ({azure_result.extraction_time_seconds:.2f}s)")
            print()

        # Generate summary
        summary = self._generate_summary(unstructured_results, azure_di_results)

        report = ComparisonReport(
            timestamp=datetime.now().isoformat(),
            total_files=len(files),
            unstructured_results=unstructured_results,
            azure_di_results=azure_di_results,
            summary=summary
        )

        return report

    def _generate_summary(self, unstruct_results: List[ExtractionResult],
                          azure_results: List[ExtractionResult]) -> Dict[str, Any]:
        """Generate comparison summary statistics"""

        def calc_stats(results: List[ExtractionResult]) -> Dict[str, Any]:
            successful = [r for r in results if r.success]
            failed = [r for r in results if not r.success]

            return {
                "total_files": len(results),
                "successful": len(successful),
                "failed": len(failed),
                "success_rate": len(successful) / len(results) if results else 0,
                "avg_extraction_time": sum(r.extraction_time_seconds for r in successful) / len(successful) if successful else 0,
                "avg_text_length": sum(r.text_length for r in successful) / len(successful) if successful else 0,
                "total_extraction_time": sum(r.extraction_time_seconds for r in results),
                "errors": [r.error for r in failed] if failed else []
            }

        unstruct_stats = calc_stats(unstruct_results)
        azure_stats = calc_stats(azure_results)

        # Determine winner
        winner = None
        if unstruct_stats["successful"] > azure_stats["successful"]:
            winner = "unstructured"
        elif azure_stats["successful"] > unstruct_stats["successful"]:
            winner = "azure_di"
        elif unstruct_stats["successful"] == azure_stats["successful"]:
            if unstruct_stats["avg_extraction_time"] < azure_stats["avg_extraction_time"]:
                winner = "unstructured"
            else:
                winner = "azure_di"

        return {
            "unstructured": unstruct_stats,
            "azure_di": azure_stats,
            "winner": winner,
            "winner_reason": self._get_winner_reason(unstruct_stats, azure_stats, winner)
        }

    def _get_winner_reason(self, unstruct_stats: Dict, azure_stats: Dict, winner: Optional[str]) -> str:
        """Explain why a particular extractor won"""
        if not winner:
            return "Tie - both performed equally"

        if unstruct_stats["successful"] != azure_stats["successful"]:
            return f"{winner} had more successful extractions"

        if winner == "unstructured":
            return f"Faster average extraction time ({unstruct_stats['avg_extraction_time']:.2f}s vs {azure_stats['avg_extraction_time']:.2f}s)"
        else:
            return f"Faster average extraction time ({azure_stats['avg_extraction_time']:.2f}s vs {unstruct_stats['avg_extraction_time']:.2f}s)"

    def save_report(self, report: ComparisonReport, output_file: str):
        """Save comparison report to JSON file"""
        report_dict = {
            "timestamp": report.timestamp,
            "total_files": report.total_files,
            "unstructured_results": [asdict(r) for r in report.unstructured_results],
            "azure_di_results": [asdict(r) for r in report.azure_di_results],
            "summary": report.summary
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Report saved to: {output_file}")

    def print_summary(self, report: ComparisonReport):
        """Print summary comparison to console"""
        print(f"\n{'='*80}")
        print(f"COMPARISON SUMMARY")
        print(f"{'='*80}")

        summary = report.summary

        print(f"\nUnstructured Library:")
        print(f"  Success Rate: {summary['unstructured']['success_rate']*100:.1f}% ({summary['unstructured']['successful']}/{summary['unstructured']['total_files']})")
        print(f"  Avg Extraction Time: {summary['unstructured']['avg_extraction_time']:.2f}s")
        print(f"  Avg Text Length: {summary['unstructured']['avg_text_length']:.0f} chars")

        print(f"\nAzure Document Intelligence:")
        print(f"  Success Rate: {summary['azure_di']['success_rate']*100:.1f}% ({summary['azure_di']['successful']}/{summary['azure_di']['total_files']})")
        print(f"  Avg Extraction Time: {summary['azure_di']['avg_extraction_time']:.2f}s")
        print(f"  Avg Text Length: {summary['azure_di']['avg_text_length']:.0f} chars")

        print(f"\n{'='*80}")
        print(f"WINNER: {summary['winner'].upper() if summary['winner'] else 'TIE'}")
        print(f"Reason: {summary['winner_reason']}")
        print(f"{'='*80}\n")


def main():
    """CLI entry point"""
    # Load environment variables from .env file
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Compare Unstructured and Azure Document Intelligence extractors"
    )
    parser.add_argument(
        "folder",
        type=str,
        help="Path to folder containing documents to extract"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="comparison_report.json",
        help="Output file for comparison report (default: comparison_report.json)"
    )
    parser.add_argument(
        "--azure-endpoint",
        type=str,
        help="Azure Document Intelligence endpoint (or set AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT env var)"
    )
    parser.add_argument(
        "--azure-key",
        type=str,
        help="Azure Document Intelligence API key (or set AZURE_DOCUMENT_INTELLIGENCE_KEY env var)"
    )

    args = parser.parse_args()

    # Create comparator
    comparator = DocumentExtractionComparator(
        azure_endpoint=args.azure_endpoint,
        azure_key=args.azure_key
    )

    # Run comparison
    try:
        report = comparator.compare_folder(args.folder)
        comparator.print_summary(report)
        comparator.save_report(report, args.output)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
