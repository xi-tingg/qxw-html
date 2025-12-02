import sys
import re
from bs4 import BeautifulSoup

# PREAMBLES
# - html headers, css
html_preamble = r"""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN"
"http://www.w3.org/TR/REC-html40/loose.dtd">
<html>
<!-- Created by Qxw 20200708 http://www.quinapalus.com -->
<head>
<title>Crossword</title>
<meta http-equiv="Content-Type" content="text/html;charset=UTF-8">
<style type="text/css">
div.bk {position:absolute;font-size:0px;border-left:black 0px solid;border-right:black 0px solid;border-top:black 36px solid;border-bottom:black 0px solid;width:36px;height:36px;}
div.nu {position:absolute;font-size:12px;font-family:sans-serif;width:32px;height:32px;pointer-events:none;z-index:20;}
div.hr {position:absolute;font-size:0px;border-top:black 1px solid;pointer-events:none;}
div.vr {position:absolute;font-size:0px;border-left:black 1px solid;pointer-events:none;}
input.cell {
    position: absolute;
    width: 36px;
    height: 36px;
    font-size: 20px;
    text-transform: uppercase;
    text-align: center;
    border: 0.5px solid #000;
    background: white;
    outline: none;
    z-index: 10;
    padding: 0;
}
input.cell:focus {
    outline: 2px solid #0078d7;
    z-index: 15;
}

.clues {
    display: flex;
    justify-content: center;
    gap: 40px;
    margin-top: 20px;
    font-family: Arial, sans-serif;
}

.crossword-wrapper {
    display: flex;
    justify-content: center;
    align-items: flex-start;
    gap: 40px;
    margin: 0 auto;
    padding: 10px;
    box-sizing: border-box;
}

.clues-column {
    display: flex;
    flex-direction: column;
    width: auto;
    font-family: Arial, sans-serif;
}

.clues-column h3 {
    text-align: center;
    margin-bottom: 10px;
    font-weight: bold;
    border-bottom: 1px solid #333;
    padding-bottom: 5px;
}

.clues-column div {
    padding: 6px 0;
    /* border-bottom: 1px dotted #ccc; */
}

.crossword-grid {
    width: 500px;
}

</style>
</head>
<body>
<center>

<div class="crossword-wrapper">
    """

cell_preamble = r"""<div class="crossword-grid">
<div style="border-width:0px;width:541px;height:541px;position:relative;">
<div style="border-width:0px;top:0px;left:0px;width:541px;height:541px;position:absolute;">"""

javascript_postamble = r"""<script>
// Store data in memory instead of localStorage
const cellData = {};

// Get all input cells and set up event listeners
const cells = document.querySelectorAll('input.cell');
cells.forEach((cell, index) => {
  const key = 'cell_' + index;
  
  // Restore value from memory if it exists
  if (cellData[key]) {
    cell.value = cellData[key];
  }
  
  // Save input to memory and auto-uppercase
  cell.addEventListener('input', (e) => {
    e.target.value = e.target.value.toUpperCase();
    cellData[key] = e.target.value;
  });
  
  // Navigate between cells with arrow keys
  cell.addEventListener('keydown', (e) => {
    const allCells = Array.from(cells);
    const currentIndex = allCells.indexOf(cell);
    
    let nextCell = null;
    
    switch(e.key) {
      case 'ArrowRight':
        nextCell = allCells[currentIndex + 1];
        break;
      case 'ArrowLeft':
        nextCell = allCells[currentIndex - 1];
        break;
      case 'ArrowDown':
        // Find cell roughly below (36px down)
        const belowCells = allCells.filter(c => {
          const thisLeft = parseInt(cell.style.left);
          const thisTop = parseInt(cell.style.top);
          const cLeft = parseInt(c.style.left);
          const cTop = parseInt(c.style.top);
          return Math.abs(cLeft - thisLeft) < 5 && cTop > thisTop;
        });
        nextCell = belowCells[0];
        break;
      case 'ArrowUp':
        // Find cell roughly above
        const aboveCells = allCells.filter(c => {
          const thisLeft = parseInt(cell.style.left);
          const thisTop = parseInt(cell.style.top);
          const cLeft = parseInt(c.style.left);
          const cTop = parseInt(c.style.top);
          return Math.abs(cLeft - thisLeft) < 5 && cTop < thisTop;
        });
        nextCell = aboveCells[aboveCells.length - 1];
        break;
    }
    
    if (nextCell && ['ArrowRight', 'ArrowLeft', 'ArrowUp', 'ArrowDown'].includes(e.key)) {
      e.preventDefault();
      nextCell.focus();
    }
  });
});
</script>
"""

# HELPER FUNCTIONS
# Helper function to extract top and left from style to use in cell generation
def extract_left_top(style):
    left  = re.search(r'left:(\d+px)', style)
    top   = re.search(r'top:(\d+px)', style)
    return (left.group(1), top.group(1))

# All cells have class bk even if they are white cells
# White cells have a border containing #FFFFFF, 
# so any border-* means it is a white cell (fake black)
def is_fake_black(style):
    return "border-top:#FFFFFF" in style or "border-left:#FFFFFF" in style or \
           "border-right:#FFFFFF" in style or "border-bottom:#FFFFFF" in style

# Parse cells according to class
def generate_cells(cells):
    cell_output = []

    for d in cells:
        cls = d.get("class", [])
        style = d.get("style", "")

        # Only care about elements with left/top position
        if "left:" not in style or "top:" not in style:
            continue

        left, top = extract_left_top(style)

        if "bk" in cls:
            if is_fake_black(style):
                # white cell disguised as black
                cell_output.append(
                    f'<input class="cell" style="left:{left};top:{top};" maxlength="1">'
                )
            else:
                # true black
                cell_output.append(
                    f'<div class="bk" style="left:{left};top:{top};"></div>'
                )
            continue

        # Clue numbers in cells
        if "nu" in cls:
            number = d.text.strip()
            cell_output.append(
                f'<div class="nu" style="left:{left};top:{top};color:000000;text-align:left">{number}</div>'
            )
            continue

        # if "hr" in cls:
        #     cell_output.append(str(d))
        #     continue

        # if "vr" in cls:
        #     cell_output.append(str(d))
        #     continue

        # Default - we only change bk and nu
        cell_output.append(str(d))

    cell_output.append(f'</div></div></div>')
    return cell_output

def across_clues_generator(across_clues):
    across_clues_ = []
    across_clues_.append(f'<div class="clues-column", style="padding-left: 3%">')
    across_clues_.append(f'<h3>Across</h3>')

    for clue in across_clues:
        clue = f'<div>{clue}</div>'
        across_clues_.append(clue)

    across_clues_.append(f'</div>')
    return across_clues_

def down_clues_generator(down_clues):
    down_clues_ = []
    down_clues_.append(f'<div class="clues-column">')
    down_clues_.append(f'<h3>Down</h3>')
    for clue in down_clues:
        clue = f'<div>{clue}</div>'
        down_clues_.append(clue)
    down_clues_.append(f'</div>')

    return down_clues_


def main():
    if len(sys.argv) != 4:
        print("Usage: python convert.py input.html clues.txt output.html")
        sys.exit(1)

    infile = sys.argv[1]
    cluesfile = sys.argv[2]
    outfile = sys.argv[3]

    across_clues = []
    down_clues = []

    with open(cluesfile, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]  # remove empty lines

    mode = None  # None, "across", or "down"
    for line in lines:
        if line.lower() == "across":
            mode = "across"
            continue
        elif line.lower() == "down":
            mode = "down"
            continue

        if mode == "across":
            across_clues.append(line)
        elif mode == "down":
            down_clues.append(line)


    with open(infile, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "lxml")

    cells = soup.select("div.bk, div.nu, div.hr, div.vr")

    output = []

    # Preambles
    output.append(html_preamble)

    # Across clues
    output.extend(across_clues_generator(across_clues))

    # Crosswsord grid
    output.append(cell_preamble)
    output.extend(generate_cells(cells))

    # Down clues
    output.extend(down_clues_generator(down_clues))

    output.append(f'</div>')
    output.append(f'</center>')

    # Postamble
    output.append(javascript_postamble)
    output.append("</body> \n</html>")

    with open(outfile, "w", encoding="utf-8") as f:
        f.write("\n".join(output))

    print("Done:", outfile)


if __name__ == "__main__":
    main()
