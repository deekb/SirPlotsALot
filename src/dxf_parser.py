def splitlines_custom(s, keepends=False):
    """
    Splits the string `s` into a list of lines, breaking at line boundaries.

    Args:
        s (str): The string to split.
        keepends (bool): If True, line breaks are included in the resulting list. Default is False.

    Returns:
        list: A list of lines.
    """
    lines = []
    line = []

    i = 0
    while i < len(s):
        if s[i] == '\n':
            if keepends:
                line.append(s[i])
            lines.append(''.join(line))
            line = []
        elif s[i] == '\r':
            if (i + 1 < len(s)) and (s[i + 1] == '\n'):
                if keepends:
                    line.append(s[i])
                    line.append(s[i + 1])
                lines.append(''.join(line))
                line = []
                i += 1  # Skip the '\n' in '\r\n'
            else:
                if keepends:
                    line.append(s[i])
                lines.append(''.join(line))
                line = []
        else:
            line.append(s[i])
        i += 1

    # Add the last line if there is any content left
    if line:
        lines.append(''.join(line))

    return lines


class DXFParser:
    def __init__(self, dxf_content):
        """
        Initializes the DXFParser with the raw DXF content.

        Args:
            dxf_content (str): The raw DXF content as a string.
        """
        self.dxf_content = dxf_content
        self.entities = []

    def parse(self):
        """
        Parses the raw DXF content and stores the entities in a structured format.
        """
        lines = splitlines_custom(self.dxf_content)

        current_entity = {}
        i = 0
        while i < len(lines):
            code = lines[i].strip()
            value = lines[i + 1].strip()
            if code == '0':  # New entity
                if current_entity:
                    self.entities.append(current_entity)
                current_entity = {'type': value}
            else:
                if code not in current_entity:
                    current_entity[code] = []
                current_entity[code].append(value)
            i += 2

        if current_entity:
            self.entities.append(current_entity)

    def get_entities(self):
        """
        Returns the parsed entities.

        Returns:
            list: A list of dictionaries representing the entities.
        """
        return self.entities

    def extract_lines(self):
        """
        Extracts line entities from the parsed DXF data.

        Returns:
            list: A list of line entities represented as lists of points.
        """
        lines = []
        for entity in self.entities:
            if entity.get('type') == 'LWPOLYLINE':
                num_points = int(entity.get('90')[0])
                points = []
                for i in range(num_points):
                    x = float(entity.get('10')[i])
                    y = float(entity.get('20')[i])
                    points.append((x, y))
                lines.append(points)
        return lines

    def combine_lines(self, lines):
        """
        Combines lines whose endpoints touch and stores all points of each combined line.

        Args:
            lines (list): A list of line entities represented as lists of points.

        Returns:
            list: A list of lists where each inner list contains the points of a combined line.
        """
        combined_lines = []
        while lines:
            line = lines.pop(0)
            combined = True
            while combined:
                combined = False
                for other_line in lines:
                    if line[-1] == other_line[0]:
                        # Combine lines by extending the current line
                        line.extend(other_line[1:])
                        lines.remove(other_line)
                        combined = True
                        break
                    elif line[0] == other_line[-1]:
                        # Combine lines by extending the current line in the opposite direction
                        line = other_line[:-1] + line
                        lines.remove(other_line)
                        combined = True
                        break
            combined_lines.append(line)
        return combined_lines
