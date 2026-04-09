Scripts for generating a Sierra SQL query that searches for records with matching OCLC numbers in the 035 tag and URLs in the 856 tag.
Workflow process: 
Using MarcEdit, export 035 and 856 tags to txt file;
Run Python script on txt file to generate SQL query;
Run SQL query;
Upload list of bib records into Create Lists;
Use Global Update to mark all of them for deletion;
Load merge file from OCLC.

Both scripts do the same thing, but sierra_sql_generator_funversion.py also displays a randomly selected literary quote each time you run it (because once I learned it was possible to do this I couldn't not do it).
