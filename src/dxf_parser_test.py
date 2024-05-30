from dxf_parser import DXFParser


if __name__ == "__main__":
    # Example raw DXF content (normally, you would read this from a file or another source)
    raw_dxf_content = open("../deploy/evans_drawing.dxf", "r").read()
    # Create parser and parse the content
    dxf_parser = DXFParser(raw_dxf_content)
    dxf_parser.parse()

    lines = dxf_parser.extract_lines()
    combined_lines = dxf_parser.combine_lines(lines)
    print(str(combined_lines).replace("],", "],\n"))

    # Print all points of each combined line
    # for line_points in combined_lines:
    #     print(line_points)

    with open("combined_output.txt", "w") as f:
        f.write(str(combined_lines).replace("],", "],\n"))
