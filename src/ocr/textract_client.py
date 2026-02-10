"""AWS Textract client for document OCR."""

from typing import Dict, List, Optional
from config.aws_config import get_textract_client
from config.settings import get_settings
from src.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class TextractClient:
    """Integrate with AWS Textract for OCR processing."""

    def __init__(self):
        """Initialize Textract client."""
        self.client = get_textract_client()
        self.confidence_threshold = settings.textract_confidence_threshold

    def analyze_document(self, document_bytes: bytes) -> Dict:
        """Analyze document with AWS Textract.

        Args:
            document_bytes: Document content as bytes

        Returns:
            Dict: Textract response with blocks
        """
        try:
            logger.info("Starting Textract document analysis")

            response = self.client.analyze_document(
                Document={"Bytes": document_bytes},
                FeatureTypes=["FORMS", "TABLES", "SIGNATURES"],
            )

            blocks = response.get('Blocks', [])
            logger.info(f"Textract analysis complete. Found {len(blocks)} blocks")
            
            # Log block type distribution
            block_types = {}
            for block in blocks:
                block_type = block.get('BlockType', 'UNKNOWN')
                block_types[block_type] = block_types.get(block_type, 0) + 1
            
            logger.info(f"Block types: {dict(sorted(block_types.items()))}")
            
            # Log sample blocks for debugging (first 5 of each type)
            if settings.debug_mode:
                logger.debug("=" * 80)
                logger.debug("SAMPLE TEXTRACT BLOCKS (first 5 of each type)")
                logger.debug("=" * 80)
                
                samples_by_type = {}
                for block in blocks:
                    block_type = block.get('BlockType', 'UNKNOWN')
                    if block_type not in samples_by_type:
                        samples_by_type[block_type] = []
                    if len(samples_by_type[block_type]) < 5:
                        samples_by_type[block_type].append(block)
                
                for block_type, sample_blocks in sorted(samples_by_type.items()):
                    logger.debug(f"\n--- {block_type} blocks ({len(sample_blocks)} samples) ---")
                    for i, block in enumerate(sample_blocks, 1):
                        logger.debug(f"  Sample {i}:")
                        logger.debug(f"    Text: {block.get('Text', 'N/A')[:100]}")
                        logger.debug(f"    Confidence: {block.get('Confidence', 0):.1f}%")
                        if block_type == 'SELECTION_ELEMENT':
                            logger.debug(f"    Status: {block.get('SelectionStatus', 'N/A')}")
                        bbox = block.get('Geometry', {}).get('BoundingBox', {})
                        if bbox:
                            logger.debug(f"    Position: top={bbox.get('Top', 0):.3f}, left={bbox.get('Left', 0):.3f}")
                
                logger.debug("=" * 80)
            
            return response

        except Exception as e:
            logger.error(f"Textract analysis failed: {str(e)}")
            raise

    def extract_text(self, blocks: List[Dict]) -> str:
        """Extract all text from Textract blocks.

        Args:
            blocks: List of Textract blocks

        Returns:
            str: Extracted text
        """
        text_parts = []

        for block in blocks:
            if block.get("BlockType") == "LINE":
                text = block.get("Text", "")
                confidence = block.get("Confidence", 0)

                if confidence >= self.confidence_threshold * 100:
                    text_parts.append(text)

        return "\n".join(text_parts)

    def extract_forms(self, blocks: List[Dict]) -> Dict[str, str]:
        """Extract key-value pairs from form fields.

        Args:
            blocks: List of Textract blocks

        Returns:
            Dict[str, str]: Dictionary of field keys to values
        """
        key_map = {}
        value_map = {}
        block_map = {}

        # Create block map for easy lookup
        for block in blocks:
            block_id = block["Id"]
            block_map[block_id] = block

            if block["BlockType"] == "KEY_VALUE_SET":
                if "KEY" in block.get("EntityTypes", []):
                    key_map[block_id] = block
                else:
                    value_map[block_id] = block

        # Extract key-value pairs
        kvs = {}
        for key_block_id, key_block in key_map.items():
            # Get key text
            key_text = self._get_text(key_block, block_map)

            # Get value text
            value_text = ""
            if "Relationships" in key_block:
                for relationship in key_block["Relationships"]:
                    if relationship["Type"] == "VALUE":
                        for value_id in relationship["Ids"]:
                            if value_id in value_map:
                                value_block = value_map[value_id]
                                value_text = self._get_text(value_block, block_map)

            if key_text and value_text:
                # Clean up key text
                key_text = key_text.strip().rstrip(":").lower()
                kvs[key_text] = value_text.strip()

        logger.info(f"Extracted {len(kvs)} key-value pairs from form")
        return kvs

    def extract_tables(self, blocks: List[Dict]) -> List[List[str]]:
        """Extract tables from document.

        Args:
            blocks: List of Textract blocks

        Returns:
            List[List[str]]: List of tables, each table is a list of rows
        """
        tables = []
        block_map = {}

        # Create block map
        for block in blocks:
            block_map[block["Id"]] = block

        # Find table blocks
        for table_idx, block in enumerate(blocks):
            if block["BlockType"] == "TABLE":
                table = self._extract_table_cells(block, block_map)
                if table:
                    tables.append(table)
                    
                    # Log table contents for debugging
                    if settings.debug_mode:
                        logger.debug(f"\nTable {table_idx + 1} extracted ({len(table)} rows):")
                        for row_idx, row in enumerate(table, 1):
                            logger.debug(f"  Row {row_idx}: {row}")

        logger.info(f"Extracted {len(tables)} tables from document")
        return tables

    def extract_checkboxes(self, blocks: List[Dict]) -> Dict[str, bool]:
        """Extract checkbox/selection elements.

        Args:
            blocks: List of Textract blocks

        Returns:
            Dict[str, bool]: Dictionary of checkbox labels to checked status
        """
        checkboxes = {}
        selected_count = 0

        for block in blocks:
            if block["BlockType"] == "SELECTION_ELEMENT":
                status = block.get("SelectionStatus") == "SELECTED"
                geometry = block.get("Geometry", {})
                checkboxes[block["Id"]] = status
                
                if status:
                    selected_count += 1
                    
                    # Log selected checkboxes with nearby text for debugging
                    if settings.debug_mode:
                        bbox = geometry.get("BoundingBox", {})
                        page = block.get("Page", 1)
                        logger.debug(f"  ✓ Selected checkbox at page={page}, top={bbox.get('Top', 0):.3f}, left={bbox.get('Left', 0):.3f}")

        logger.info(f"Extracted {len(checkboxes)} checkboxes from document ({selected_count} selected)")
        return checkboxes

    def detect_signatures(self, blocks: List[Dict]) -> List[Dict]:
        """Detect signature blocks in document.

        Args:
            blocks: List of Textract blocks

        Returns:
            List[Dict]: List of signature blocks with metadata
        """
        signatures = []

        for block in blocks:
            if block["BlockType"] == "SIGNATURE":
                confidence = block.get("Confidence", 0)
                if confidence >= self.confidence_threshold * 100:
                    signatures.append(
                        {
                            "id": block["Id"],
                            "confidence": confidence / 100.0,
                            "geometry": block.get("Geometry", {}),
                        }
                    )

        logger.info(f"Detected {len(signatures)} signatures in document")
        return signatures

    def _get_text(self, block: Dict, block_map: Dict) -> str:
        """Get text from a block and its children.

        Args:
            block: Textract block
            block_map: Map of block IDs to blocks

        Returns:
            str: Extracted text
        """
        text_parts = []

        if "Relationships" in block:
            for relationship in block["Relationships"]:
                if relationship["Type"] == "CHILD":
                    for child_id in relationship["Ids"]:
                        if child_id in block_map:
                            child = block_map[child_id]
                            if (
                                child["BlockType"] == "WORD"
                                or child["BlockType"] == "LINE"
                            ):
                                text = child.get("Text", "")
                                if text:
                                    text_parts.append(text)

        return " ".join(text_parts)

    def _extract_table_cells(
        self, table_block: Dict, block_map: Dict
    ) -> List[List[str]]:
        """Extract cells from a table block.

        Args:
            table_block: Table block from Textract
            block_map: Map of block IDs to blocks

        Returns:
            List[List[str]]: Table data as list of rows
        """
        rows = {}

        if "Relationships" in table_block:
            for relationship in table_block["Relationships"]:
                if relationship["Type"] == "CHILD":
                    for cell_id in relationship["Ids"]:
                        if cell_id in block_map:
                            cell = block_map[cell_id]
                            if cell["BlockType"] == "CELL":
                                row_index = cell.get("RowIndex", 0)
                                col_index = cell.get("ColumnIndex", 0)
                                cell_text = self._get_text(cell, block_map)

                                if row_index not in rows:
                                    rows[row_index] = {}
                                rows[row_index][col_index] = cell_text

        # Convert to list of lists
        table_data = []
        for row_index in sorted(rows.keys()):
            row = rows[row_index]
            row_data = [row.get(col_index, "") for col_index in sorted(row.keys())]
            table_data.append(row_data)

        return table_data
