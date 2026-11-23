import json
import math

import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network


# ----------------------------------------------------------------------
# Canvas overlay (runs inside the generated vis-network page).
# Draws the initial-state arrow and all self-loops in afterDrawing, so
# they follow dragging / zooming / panning without helper nodes.
# ----------------------------------------------------------------------
_OVERLAY_JS = """
<script type="text/javascript">
(function () {
  var CFG = __CONFIG__;

  function init() {
    if (typeof network === "undefined") {
      setTimeout(init, 50);
      return;
    }

    var LINE = "#91a0b5";
    var START = "#d69b45";

    function angleDiff(a, b) {
      var d = Math.abs(a - b) % (2 * Math.PI);
      return d > Math.PI ? 2 * Math.PI - d : d;
    }

    function arrowHead(ctx, tipX, tipY, dx, dy, size, color) {
      var len = Math.sqrt(dx * dx + dy * dy) || 1;
      dx /= len; dy /= len;
      var px = -dy, py = dx;
      ctx.beginPath();
      ctx.moveTo(tipX, tipY);
      ctx.lineTo(tipX - dx * size + px * size * 0.5,
                 tipY - dy * size + py * size * 0.5);
      ctx.lineTo(tipX - dx * size - px * size * 0.5,
                 tipY - dy * size - py * size * 0.5);
      ctx.closePath();
      ctx.fillStyle = color;
      ctx.fill();
    }

    function ellipsePoint(box, phi) {
      var a = (box.right - box.left) / 2;
      var b = (box.bottom - box.top) / 2;
      var cx = (box.right + box.left) / 2;
      var cy = (box.bottom + box.top) / 2;
      var r = (a * b) / Math.sqrt(
        Math.pow(b * Math.cos(phi), 2) + Math.pow(a * Math.sin(phi), 2));
      return { x: cx + r * Math.cos(phi), y: cy + r * Math.sin(phi) };
    }

    function chooseLoopAngle(id) {
      var me = network.getPosition(id);
      var blocked = [];
      CFG.links.forEach(function (link) {
        var other = null;
        if (link[0] === id) other = link[1];
        else if (link[1] === id) other = link[0];
        if (other !== null && other !== id) {
          var p = network.getPosition(other);
          blocked.push(Math.atan2(p.y - me.y, p.x - me.x));
        }
      });
      if (id === CFG.initial) blocked.push(Math.PI);  // initial arrow on left

      var up = -Math.PI / 2;
      var best = up, bestScore = -Infinity;
      for (var deg = 0; deg < 360; deg += 15) {
        var ang = up + deg * Math.PI / 180;
        var minDist = Math.PI;
        blocked.forEach(function (b) {
          minDist = Math.min(minDist, angleDiff(ang, b));
        });
        var score = Math.min(minDist, Math.PI / 2)
                    - 0.05 * angleDiff(ang, up);
        if (score > bestScore + 1e-9) { bestScore = score; best = ang; }
      }
      return best;
    }

    function drawStart(ctx) {
      if (!CFG.initial) return;
      var box = network.getBoundingBox(CFG.initial);
      var y = (box.top + box.bottom) / 2;
      var tipX = box.left - 2;
      var fromX = tipX - 42;
      ctx.save();
      ctx.beginPath();
      ctx.moveTo(fromX, y);
      ctx.lineTo(tipX - 8, y);
      ctx.strokeStyle = START;
      ctx.lineWidth = 2.5;
      ctx.stroke();
      arrowHead(ctx, tipX, y, 1, 0, 11, START);
      ctx.restore();
    }

    function drawLoop(ctx, loop) {
      var box = network.getBoundingBox(loop.id);
      var theta = chooseLoopAngle(loop.id);
      var dir = { x: Math.cos(theta), y: Math.sin(theta) };
      var perp = { x: -dir.y, y: dir.x };
      var h = 62;

      var p1 = ellipsePoint(box, theta - 0.55);
      var p2 = ellipsePoint(box, theta + 0.55);
      var c1 = { x: p1.x + dir.x * h - perp.x * 12,
                 y: p1.y + dir.y * h - perp.y * 12 };
      var c2 = { x: p2.x + dir.x * h + perp.x * 12,
                 y: p2.y + dir.y * h + perp.y * 12 };

      ctx.save();
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.bezierCurveTo(c1.x, c1.y, c2.x, c2.y, p2.x, p2.y);
      ctx.strokeStyle = LINE;
      ctx.lineWidth = 2;
      ctx.stroke();
      arrowHead(ctx, p2.x, p2.y, p2.x - c2.x, p2.y - c2.y, 10, LINE);

      // label just beyond the loop apex (above it for upward loops)
      var apex = {
        x: (p1.x + 3 * c1.x + 3 * c2.x + p2.x) / 8,
        y: (p1.y + 3 * c1.y + 3 * c2.y + p2.y) / 8
      };
      var lx = apex.x + dir.x * 6;
      var ly = apex.y + dir.y * 6;
      ctx.font = "14px Inter, Arial, sans-serif";
      ctx.textAlign = dir.x > 0.4 ? "left" : (dir.x < -0.4 ? "right" : "center");
      ctx.textBaseline = dir.y < -0.4 ? "bottom" : (dir.y > 0.4 ? "top" : "middle");
      ctx.lineJoin = "round";
      ctx.lineWidth = 4;
      ctx.strokeStyle = "#ffffff";
      ctx.strokeText(loop.label, lx, ly);
      ctx.fillStyle = "#53647d";
      ctx.fillText(loop.label, lx, ly);
      ctx.restore();
    }

    network.on("afterDrawing", function (ctx) {
      drawStart(ctx);
      CFG.loops.forEach(function (loop) { drawLoop(ctx, loop); });
    });

    // Fit inside the container, leaving room for loops and the arrow.
    network.fit({ animation: false });
    network.moveTo({ scale: Math.min(network.getScale() * 0.78, 1.2) });
    network.redraw();
  }

  init();
})();
</script>
"""


def _transition_label(row, symbol, machine_type):
    """Return (destination, label) for one state/symbol, or None."""

    if machine_type == "mealy":

        next_col = f"Input {symbol} - Next State"

        if next_col not in row:
            return None

        output = row.get(f"Input {symbol} - Output", "?")

        return str(row[next_col]), f"{symbol}/{output}"

    next_col = next(
        (
            column
            for column in (
                f"Input {symbol}",
                f"Input {symbol} - Next State",
            )
            if column in row
        ),
        None,
    )

    if next_col is None:
        return None

    return str(row[next_col]), str(symbol)


def render_state_diagram(
    rows,
    inputs,
    initial_state,
    machine_type,
    diagram_key="machine",
    layout_states=None,
):

    if not rows:
        st.info("No states are available to display yet.")
        return

    machine_type = str(machine_type).strip().lower()
    initial_state = str(initial_state)

    visible_states = list(
        dict.fromkeys(str(row["State"]) for row in rows)
    )

    states = list(
        dict.fromkeys(
            str(state) for state in (layout_states or visible_states)
        )
    )

    for state in visible_states:
        if state not in states:
            states.append(state)

    if not states:
        st.info("No states are available to display.")
        return

    net = Network(
        height="500px",
        width="100%",
        directed=True,
        bgcolor="#ffffff",
        font_color="#34445e",
        notebook=False,
        cdn_resources="in_line",
    )

    # --------------------------------------------------
    # STATE POSITIONS (circular layout over all states,
    # so positions stay stable while steps are revealed)
    # --------------------------------------------------

    radius = max(170, 65 * len(states))
    positions = {}

    for index, state in enumerate(states):

        angle = 2 * math.pi * index / len(states) - math.pi / 2

        positions[state] = (
            int(radius * math.cos(angle)),
            int(radius * math.sin(angle)),
        )

    row_lookup = {str(row["State"]): row for row in rows}

    # --------------------------------------------------
    # NODES
    # --------------------------------------------------

    for state in visible_states:

        row = row_lookup[state]
        x, y = positions[state]

        if machine_type == "moore":
            label = f"{state}/{row.get('Output', '?')}"
            background, border = "#e5f5f1", "#63ad9d"
        else:
            label = state
            background, border = "#e9edff", "#8291d8"

        is_initial = state == initial_state

        if is_initial:
            background, border = "#fff0dc", "#e3a04e"

        net.add_node(
            state,
            label=label,
            title=label,
            x=x,
            y=y,
            physics=False,
            shape="ellipse",
            color={"background": background, "border": border},
            borderWidth=3 if is_initial else 2,
            margin=10,
            font={"color": "#34445e", "size": 17, "face": "Inter"},
        )

    # --------------------------------------------------
    # COLLECT TRANSITIONS (straight from the table)
    # --------------------------------------------------

    transition_groups = {}

    for row in rows:

        source = str(row["State"])

        for symbol in inputs:

            parsed = _transition_label(row, symbol, machine_type)

            if parsed is None:
                continue

            destination, label = parsed

            if destination not in visible_states:
                continue

            labels = transition_groups.setdefault(
                (source, destination), []
            )

            if label not in labels:
                labels.append(label)

    # --------------------------------------------------
    # EDGES (self-loops are drawn by the canvas overlay)
    # --------------------------------------------------

    edge_font = {
        "color": "#53647d",
        "size": 14,
        "face": "Inter",
        "align": "top",
        "strokeWidth": 4,
        "strokeColor": "#ffffff",
    }

    edge_color = {"color": "#91a0b5", "highlight": "#6878d6"}

    loops = []
    links = []

    for (source, destination), labels in transition_groups.items():

        edge_label = ", ".join(labels)

        if source == destination:
            loops.append({"id": source, "label": edge_label})
            continue

        links.append([source, destination])

        # Both directions use the SAME curve type: vis-network measures the
        # curve relative to edge direction, so the two bow to opposite sides.
        reverse_exists = (destination, source) in transition_groups

        net.add_edge(
            source,
            destination,
            label=edge_label,
            arrows="to",
            color=edge_color,
            width=2,
            smooth={
                "enabled": True,
                "type": "curvedCW",
                "roundness": 0.3 if reverse_exists else 0.12,
            },
            font=edge_font,
        )

    # --------------------------------------------------
    # OPTIONS
    # --------------------------------------------------

    net.set_options("""
    {
      "physics": { "enabled": false },
      "interaction": {
        "dragNodes": true,
        "dragView": true,
        "zoomView": true,
        "hover": true,
        "navigationButtons": false,
        "selectConnectedEdges": false
      },
      "edges": {
        "arrows": { "to": { "enabled": true, "scaleFactor": 0.8 } }
      }
    }
    """)

    # --------------------------------------------------
    # DISPLAY
    # --------------------------------------------------

    config = {
        "initial": initial_state if initial_state in visible_states else None,
        "loops": loops,
        "links": links,
    }

    overlay = _OVERLAY_JS.replace("__CONFIG__", json.dumps(config))

    html = net.generate_html()

    head, sep, tail = html.rpartition("</body>")

    html = head + overlay + sep + tail if sep else html + overlay

    components.html(html, height=520, scrolling=False)