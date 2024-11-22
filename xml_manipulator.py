import os
import re
import sys
import xml.etree.ElementTree as ET

symbol_map = {
    "f": "-null",
    "l": "-null",
    "v": "-null",
    "va": "-null",
    "vb": "-null",
    "z": "-null",
    "r_i": "",
    "r_ii": "",
    "r_iii": "",
    "p_i": "",
    "p_ii": "",
    "p_iii": "",
}

def add_xml_declaration(file_path):
    xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'

    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    # Add XML declaration if not present
    if not content.startswith(xml_declaration):
        content = xml_declaration + content
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)
        print(f"Added XML declaration to {file_path}")


def remove_seg_pattern(file_path):
    seg_pattern = re.compile(r'(<seg n="\d+">)\[\d+\]')

    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    # Remove the pattern <seg n="X">[Y]
    new_content = seg_pattern.sub(r"\1", content)

    if new_content != content:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(new_content)
        print(f"Removed pattern from {file_path}")

def add_chapter_type_and_wrap_head(file_path):
    file_prefix = os.path.basename(file_path).replace("_completo.xml", "").lower()
    # Parse the XML file
    ET.register_namespace('', "http://www.tei-c.org/ns/1.0")
    tree = ET.parse(file_path)
    root = tree.getroot()

    namespace = {"tei": "http://www.tei-c.org/ns/1.0"}

    # Find all <div> elements
    for div in root.findall(".//tei:div", namespace):
        # Ensure type="chapter" attribute
        div.set("type", "chapter")

        # Add xml:id="r-i-<n>" attribute based on the n attribute
        n_value = div.get("n", "")
        if n_value:
            
            div.set("{http://www.w3.org/XML/1998/namespace}id", f"{file_prefix}{symbol_map[file_prefix]}-{n_value}")
            # div.set("{http://www.w3.org/XML/1998/namespace}id", f"p-i-{n_value}")

        # Process the <head> inside the <div>
        head = div.find("tei:head", namespace)
        if head is not None:
            existing_seg = head.find("tei:seg", namespace)
            if existing_seg is None:
                # Wrap head's content in a <seg> with xml:id = div's id + "-titolo"
                div_id = div.get("{http://www.w3.org/XML/1998/namespace}id", "")
                seg_id = f"{div_id}-titolo"
                seg = ET.Element(f"{{{namespace['tei']}}}seg", attrib={"xml:id": seg_id})

                # Move head's content into the <seg>
                if head.text:
                    seg.text = head.text
                    head.text = None

                # Insert the <seg> into <head>
                head.append(seg)

    # Write back to the file
    tree.write(file_path, encoding="utf-8", xml_declaration=True)
    print(f"Processed <div> elements in {file_path}")

def process_xml_files(folder_path):
    # Check if folder path exists
    if not os.path.isdir(folder_path):
        print(f"Error: The folder '{folder_path}' does not exist.")
        return

    # Process each XML file in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith(".xml"):
            file_path = os.path.join(folder_path, filename)
            add_chapter_type_and_wrap_head(file_path)
            # Apply both functions to each file
            # add_xml_declaration(file_path)
            # remove_seg_pattern(file_path)
            
def create_combined_tei_file(folder_path, output_file):
    # XML template for the header of the new TEI file
    header = """<?xml version="1.0" encoding="UTF-8"?>
<?xml-model href="http://www.tei-c.org/release/xml/tei/custom/schema/relaxng/tei_all.rng" type="application/xml" schematypens="http://relaxng.org/ns/structure/1.0"?>
<?xml-model href="http://www.tei-c.org/release/xml/tei/custom/schema/relaxng/tei_all.rng" type="application/xml" schematypens="http://purl.oclc.org/dsdl/schematron"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
   <teiHeader>
      <fileDesc>
         <titleStmt>
            <title>Title</title>
         </titleStmt>
         <publicationStmt>
            <p>Publication Information</p>
         </publicationStmt>
         <sourceDesc>
            <p>Information about the source</p>
         </sourceDesc>
      </fileDesc>
   </teiHeader>
   <text>
      <body>
         <listApp xml:id="MP_listApp">
"""

    footer = """        </listApp>
      </body>
   </text>
</TEI>
"""

    app_pattern = re.compile(r'<app from="[^"]+">.*?</app>', re.DOTALL)
    collected_apps = []

    # Iterate over all XML files in the specified folder
    for filename in os.listdir(folder_path):
        if filename.endswith(".xml"):
            file_path = os.path.join(folder_path, filename)
            file_base = os.path.splitext(filename)[0]  # Get filename without extension

            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()

                # Find all <app from="...">...</app> matches
                matches = app_pattern.findall(content)
                
                # Modify each match to include the filename in the `from` attribute
                for match in matches:
                    modified_match = re.sub(r'from="[^"]+"', f'from="#{file_base}"', match)
                    collected_apps.append(modified_match)

    # Sort apps to place those ending with "-titolo" first
    collected_apps.sort(key=lambda x: (("-titolo" not in x), x))

    # Write the new TEI file
    with open(output_file, "w", encoding="utf-8") as output:
        output.write(header)
        for app in collected_apps:
            output.write(f"            {app}\n")
        output.write(footer)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <folder_path>")
    else:
        folder_path = sys.argv[1]
        process_xml_files(folder_path)
        # create_combined_tei_file(folder_path, "apparati_RAM.xml")
