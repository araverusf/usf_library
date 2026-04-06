import re
import csv



def extract_oclc_numbers(oclc_field):
    """
    Extract all OCLC numbers from a 035 field.
    
    Args:
        oclc_field: String containing OCLC data like "\\$a(OCoLC)37104052$z(OCoLC)40611891..."
    
    Returns:
        List of OCLC numbers
    """
    # Find all patterns like (OCoLC)12345678
    pattern = r'\(OCoLC\)(\d+)'
    matches = re.findall(pattern, oclc_field)
    return matches


def extract_urls(url_field):
    """
    Extract all URLs from an 856 field.
    URLs are separated by semicolons.
    
    Args:
        url_field: String containing one or more URLs separated by semicolons
    
    Returns:
        List of URLs
    """
    # Split on semicolon to get individual URLs
    urls = url_field.split(';')
    # Strip whitespace and filter out empty strings
    urls = [url.strip() for url in urls if url.strip()]
    return urls


def escape_sql_like(value):
    """
    Escape special characters for SQL LIKE clauses.
    
    Args:
        value: String to escape
    
    Returns:
        Escaped string safe for use in LIKE clauses
    """
    # Escape backslashes first (since we'll be adding more)
    value = value.replace('\\', '\\\\')
    # Escape single quotes (SQL string delimiter)
    value = value.replace("'", "''")
    # Escape LIKE wildcards
    value = value.replace('%', '\\%')
    value = value.replace('_', '\\_')
    
    return value


def parse_input_file(input_file):
    """
    Parse the tab-delimited input file containing OCLC numbers and URLs.
    
    Args:
        input_file: Path to tab-delimited text file
    
    Returns:
        List of tuples (oclc_numbers_list, urls_list)
    """
    records = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        # Use csv reader for tab-delimited files
        reader = csv.reader(f, delimiter='\t')
        
        # Skip header row
        next(reader, None)
        
        for row in reader:
            if len(row) >= 2:
                oclc_field = row[0].strip('"')  # Remove surrounding quotes
                url_field = row[1].strip('"')  # Remove surrounding quotes
                
                # Extract OCLC numbers from the field
                oclc_numbers = extract_oclc_numbers(oclc_field)
                
                # Extract all URLs from the field
                urls = extract_urls(url_field)
                
                if oclc_numbers and urls:
                    records.append((oclc_numbers, urls))
    
    return records


def generate_sierra_sql_query(input_file, output_file=None):
    """
    Generate a Sierra ILS SQL query to search for bib records by OCLC numbers and URLs.
    
    Args:
        input_file: Path to tab-delimited text file containing OCLC and URL data
        output_file: Optional path to save the generated SQL query
    
    Returns:
        String containing the generated SQL query
    """
    
    # Parse the input file
    records = parse_input_file(input_file)
    
    if not records:
        print("ERROR: No valid records found in input file!")
        return None
    
    # Start building the SQL query
    sql_query = """SELECT DISTINCT
    'b' || b.record_num || 'a' AS bibnumber, 
    v_035.field_content AS oclcnumber,
    v_856.field_content AS url,
    bibloc.location_code AS locationcode
FROM sierra_view.bib_view b
INNER JOIN sierra_view.varfield v_035 ON b.id = v_035.record_id
INNER JOIN sierra_view.varfield v_856 ON b.id = v_856.record_id
INNER JOIN sierra_view.bib_record_location bibloc ON b.id = bibloc.bib_record_id
WHERE bibloc.location_code = 'gint'
    AND v_035.marc_tag = '035'
    AND v_856.marc_tag = '856'
    AND (
"""
    
    # Build conditions for each record
    conditions = []
    
    for oclc_numbers, urls in records:
        # Build OCLC number conditions (OR multiple OCLC numbers together)
        oclc_conditions = []
        for oclc in oclc_numbers:
            oclc_conditions.append(f"v_035.field_content LIKE '%{oclc}%'")
        
        # Combine OCLC conditions with OR
        oclc_part = " OR ".join(oclc_conditions)
        
        # If there are multiple OCLC numbers, wrap in parentheses
        if len(oclc_numbers) > 1:
            oclc_part = f"({oclc_part})"
        
        # Build URL conditions (OR multiple URLs together)
        url_conditions = []
        for url in urls:
            escaped_url = escape_sql_like(url)
            url_conditions.append(f"v_856.field_content LIKE '%{escaped_url}%' ESCAPE '\\'")
        
        # Combine URL conditions with OR
        url_part = " OR ".join(url_conditions)
        
        # If there are multiple URLs, wrap in parentheses
        if len(urls) > 1:
            url_part = f"({url_part})"
        
        # Build the complete condition for this record (OCLC AND URL)
        record_condition = f"""        (
            {oclc_part}
            AND {url_part}
        )"""
        
        conditions.append(record_condition)
    
    # Join all record conditions with OR
    sql_query += "\n        OR\n".join(conditions)
    
    # Close the query
    sql_query += """
    );"""
    
    # Save to file if output path provided
    if output_file:
        with open(output_file, 'w') as f:
            f.write(sql_query)
        print(f"SQL query saved to: {output_file}")
    
    # Print statistics
    print(f"\nGenerated SQL query for {len(records)} records")
    print(f"\nFirst 3 records:")
    for i, (oclc_numbers, urls) in enumerate(records[:3], 1):
        print(f"  {i}. OCLC numbers ({len(oclc_numbers)}): {oclc_numbers[:3]}{'...' if len(oclc_numbers) > 3 else ''}")
        print(f"     URLs ({len(urls)}):")
        for j, url in enumerate(urls[:2], 1):
            print(f"       {j}. {url[:70]}{'...' if len(url) > 70 else ''}")
        if len(urls) > 2:
            print(f"       ... and {len(urls) - 2} more")
    
    return sql_query


# Example usage
if __name__ == "__main__":
    import sys
    import os
    
    # Check if input file was provided as command line argument
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        
        # Check if output file/directory was also provided
        if len(sys.argv) > 2:
            output_arg = sys.argv[2]
            
            # Check if it's a directory or a file path
            if os.path.isdir(output_arg):
                # It's a directory, create filename in that directory
                base_name = os.path.basename(input_file)
                if base_name.endswith('.txt'):
                    filename = base_name.replace('.txt', '_query.sql')
                else:
                    filename = base_name + '_query.sql'
                output_file = os.path.join(output_arg, filename)
            else:
                # It's a full file path
                output_file = output_arg
        else:
            # No output specified, use current directory
            base_name = os.path.basename(input_file)
            if base_name.endswith('.txt'):
                output_file = base_name.replace('.txt', '_query.sql')
            else:
                output_file = base_name + '_query.sql'
    else:
        # Prompt user for input file name
        input_file = input("Enter the name of your input text file: ")
        
        # Ask if user wants to specify output location
        output_choice = input("Specify output location? (y/n, default=current directory): ").lower()
        
        if output_choice == 'y':
            output_arg = input("Enter output directory or full file path: ")
            
            if os.path.isdir(output_arg):
                # It's a directory
                base_name = os.path.basename(input_file)
                if base_name.endswith('.txt'):
                    filename = base_name.replace('.txt', '_query.sql')
                else:
                    filename = base_name + '_query.sql'
                output_file = os.path.join(output_arg, filename)
            else:
                # It's a full file path
                output_file = output_arg
        else:
            # Use current directory
            base_name = os.path.basename(input_file)
            if base_name.endswith('.txt'):
                output_file = base_name.replace('.txt', '_query.sql')
            else:
                output_file = base_name + '_query.sql'
    
    # Generate the query
    sql_query = generate_sierra_sql_query(input_file, output_file)
    
    if sql_query:
        print("\n" + "="*70)
        print(f"Done! Your SQL query is ready in: {output_file}")
        print("="*70)
   


