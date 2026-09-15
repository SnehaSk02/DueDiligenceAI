from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter
#Text chunking
def chunk_text(text:str, chunk_size:int=1000, chunk_overlap:int =150)->List[str]:
    """ Split normal document text using LangChain's RecursiveCharacterTextSplitter. 
    The splitter tries to preserve larger text structures before splitting into smaller units. Splitting priority: 
    1. Paragraph 
    2. Line 
    3. Sentence/space 
    4. Character 
    """
    if not text:
        return []

    splitter = RecursiveCharacterTextSplitter(chunk_size = chunk_size,
                                              chunk_overlap = chunk_overlap,
                                              separators=[
                                                  "\n\n",
                                                  "\n",
                                                  ". ",
                                                  " ",
                                                  ""
                                              ],
                                              length_function = len,
                                              is_separator_regex=False)

    chunks = splitter.split_text(text)

    return[
        chunk.strip() for chunk in chunks if chunk.strip()]


#Table cell cleaning
def clean_table_cell(cell) -> str:
    """
    clean individual table cell
    """
    if cell is None:
        return ""
    return(
        str(cell)
        .replace("\n"," ")
        .strip()
    )

#Table conversion
def table_to_rows(table:Dict)->List[str]:
    headers = table.get("headers",[])
    rows= table.get("rows",[])

    cleaned_headers = [clean_table_cell(cell) for cell in headers]

    table_rows= []

    #add header
    if cleaned_headers:
        table_rows.append(" | ".join(cleaned_headers))
    #add data rows 
    for row in rows:
        cleaned_row =[ clean_table_cell(cell) for cell in row]

    #skip completely empty rows
        if not any (cleaned_row):
            continue
        table_rows.append(" | ".join(cleaned_row))

    return table_rows


#Table chunking
def chunk_table(table:Dict, chunk_size:int =1000) ->List[str]:
    """ Split a table into chunks while preserving row-column relationships. 
    The header is repeated in every chunk. 
    Tables are split by rows, not arbitrary characters. """

    table_rows = table_to_rows(table)

    if not table_rows:
        return []

    #first row is the header
    header = table_rows[0]

    #remaining rows are data
    data_rows = table_rows[1:]

    chunks=[]
    current_rows= []

    for row in data_rows:
        candidate_rows=([header] + current_rows + [row])
        candidate_text = "\n".join(candidate_rows)
        #current row fits into the chunk
        if len(candidate_text) <=chunk_size:
            current_rows.append(row)
        else:
            #save current chunk
            if current_rows:
                chunks.append("\n".join([header] + current_rows))

                #start a new chunk
                current_rows = [row]

    #save remaining rows
    if current_rows:
        chunks.append("\n".join([header] + current_rows))

    #table containing only a header
    if not data_rows:
        chunks.append(header)
    return chunks

#Main chunk builder
def build_chunks(parsed_pages:List[Dict],
                 case_id:int,
                 document_id:int,
                 document_type: str,
                 chunk_size:int=1000,
                 chunk_overlap:int=150) ->List[Dict]:
    """ Build RAG-ready chunks from parsed PDF pages. 
    Text: LangChain RecursiveCharacterTextSplitter 
    Tables: Custom table-aware row-based chunking 
    Images: Currently detected and preserved at page level, but not converted into RAG chunks because image understanding has not been implemented yet. 
    Metadata is preserved for provenance. 
    """
    chunks = []
    chunk_index = 0
    for page in parsed_pages:
        page_number = page["page_number"]

        #text chunks
        if page.get("has_text", False):
            text_chunks = chunk_text(text=page.get("text",""),
                                                   chunk_size = chunk_size,
                                                   chunk_overlap=chunk_overlap)

            for text in text_chunks:
                if not text:
                    continue

                chunks.append({
                    "case_id" : case_id,
                    "document_id": document_id,
                    "document_type" : document_type,
                    "page_number" : page_number,
                    "content_type" : "text",
                    "chunk_index" : chunk_index,
                    "text" : text
                })
                chunk_index += 1

        #table chunks
        if page.get("has_table",False):
            for table in page.get("tables",[]):
                #skip failed table extraction
                if (table.get("extraction_status")!="success"):
                    continue

                table_chunks = chunk_table(table=table, chunk_size=chunk_size)
                for table_text in table_chunks:
                    if not table_text:
                        continue
                    chunks.append({
                        "case_id" : case_id,
                        "document_id" : document_id,
                        "document_type" : document_type,
                        "page_number" : page_number,
                        "content_type" : "table",
                        "table_index" : table.get("table_index"),
                        "chunk_index" : chunk_index,
                        "text" : table_text    
                    })
                    chunk_index+=1
    return chunks