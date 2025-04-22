import gradio as gr

def noop(*_):
    pass

with gr.Blocks(title="Font‑size changer") as demo:
    gr.Markdown("### Highlight some text, then pick a size")

    editor = gr.HTML(
        """
        <div id="editor"
             contenteditable="true"
             style="border:1px solid #ccc; padding:12px; min-height:150px; line-height:1.4;">
          Type or paste text here … then select a fragment and change its size 🖱️
        </div>
        """
    )

    # Radio returns strings like "12pt"
    size = gr.Radio(["12pt", "14pt", "16pt"], value="12pt", label="Font size (pt)")

    size.change(
        fn=noop,                # backend stub (no server work needed)
        inputs=[size],
        outputs=None,
        js="""
        (pt) => {
console.log('applySize called with', pt);
            const sel = window.getSelection();
            if (!sel.rangeCount || sel.isCollapsed) {
                alert('Select some text first!');
                return;
            }
            const range = sel.getRangeAt(0);

            // Try the simple path first …
            try {
                const span = document.createElement('span');
                span.style.fontSize = pt;
                range.surroundContents(span);
            } catch (e) {
                // … and if the selection crosses element boundaries, fall back
                const frag = range.extractContents();
                const span = document.createElement('span');
                span.style.fontSize = pt;
                span.appendChild(frag);
                range.insertNode(span);
            }

            // Optional: clear selection so the user sees the change immediately
            sel.removeAllRanges();
        }
        """
    )

demo.launch()
