import gradio as gr
import pathlib, requests

# Placeholder variables for initial OCR output and cleaned text
ocr_raw_text = "Sample OCR output text extracted from the uploaded document."
gpt_cleaned_text = "The text after GPT-based cleanup, ready for editing and formatting."

def make_upload_file_name(local_path: pathlib.Path) -> str:
    """
    Convert /any/local/file.ext  -->  temp.ext   (optionally prefixed by folder/)
    """
    suffix     = local_path.suffix              # keeps leading dot, e.g. ".pdf"
    temp_name  = f"temp{suffix or ''}"          # "temp" if no extension
    
    return temp_name

# ---- 4)  UPLOAD FUNCTION FOR GRADIO -----------------------------------------
async def process_file(file: gr.FileData | pathlib.Path):
    global ocr_raw_text, gpt_cleaned_text

    try:
        """Receives a Gradio file object (or path) and uploads it to GCS."""
        local_path = pathlib.Path(file.name if hasattr(file, "name") else str(file))
        upload_file_name  = make_upload_file_name(local_path)
                         
        with local_path.open("rb") as f:          
            files = { "file": (upload_file_name, f, "application/octet-stream")}  # binary data
            data = {"filename": upload_file_name}                                 # file name
   
            resp = requests.post(
                    "https://israi.app.n8n.cloud/webhook/ocr-text1",
                    data = data,
                    files = files
            )
        
        resp.raise_for_status()
        ocr_text = resp.text     
    except Exception as e:
        ocr_text = f"❌ OCR request failed: {e}"
        
    ocr_raw_text = ocr_text
    return ocr_text

async def clean_ocr_result() -> str:
    global gpt_cleaned_text, ocr_raw_text
    
    try:
        resp = requests.post(
                    "https://israi.app.n8n.cloud/webhook/clean-ocr-result",
                    json={"ocr_output": ocr_raw_text})
        resp.raise_for_status()

        clean_text = resp.text      # adjust if your flow returns JSON
    except Exception as e:
        clean_text = f"❌ GPT process failed: {e}"
        
    gpt_cleaned_text = clean_text    
    
    return clean_text
                        
# .  Callback: layout summary  +  runtime CSS for edit_box ──────────────
def apply_layout(font_size, line_mode, line_height):
    summary = (
        f"[Layout Settings Applied]\n"
        f"Font Size: {font_size}\n"
        f"Line Mode: {line_mode}\n"
        f"Line Height: {line_height}"
    )
    
    css = f"""
    <style>
      #edit_box textarea {{
          line-height: {line_height} !important;
          font-size: {font_size};
      }}
    </style>
    """
    
    # gr.HTML(css)
    return summary, gr.update(value=css)

# Gradio Interface starts here
with gr.Blocks() as demo:
    
    style_box = gr.HTML("", visible=False)

    # Header Section
    gr.Markdown("## Planning & Building Notices – OCR Interface")
    gr.Markdown("Upload a scanned PDF or image of a statutory notice. View OCR result, edit, and apply formatting rules.")
    
    with gr.Row():
        # Upload Section
        with gr.Column():
            upload = gr.File(label="📄 Upload PDF or Image", file_types=[".pdf", ".png", ".PNG", ".jpg", ".jpeg"])
            with gr.Row():
                gr.Markdown("#### Waiting for upload...")
                process_btn = gr.Button("Process OCR", scale=0, min_width=160)
            
            gr.Markdown("---")

            # Main Content Area - two columns side by side
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Original OCR Text")
                    ocr_box = gr.Textbox(
                                value=ocr_raw_text, 
                                lines=12, 
                                interactive=False, 
                                rtl=True, 
                                text_align="right",
                                label="",
                                elem_id="ocr_box"
                                )

                with gr.Column():
                    gr.Markdown("### Cleaned & Editable Text")
                    edit_box = gr.Textbox(
                        value=gpt_cleaned_text, 
                        lines=12, 
                        interactive=True,
                        rtl=True, 
                        text_align="right",
                        label="",
                        elem_id="edit_box" 
                        )
                    # gr.Button("🔄 Restore Original")
                    clean_btn = gr.Button("✅ Create Formatted Document")
                
        with gr.Column(scale=0):
            font_size = gr.Radio(["5.5pt", "7pt", "10pt"], label="Font Size", value="7pt", elem_id="font_size", interactive=True,)
            line_mode = gr.Radio(["Continuous", "Spaced"], label="Line Mode", value="Spaced", elem_id="line_mode", interactive=True,)
            line_height = gr.Radio(["7pt", "9pt", "12pt"], label="Line Height", value="12pt", elem_id="line_height", interactive=True,)
            apply_btn = gr.Button("Apply Layout Rules")
            layout_result = gr.Textbox(label="Layout Summary", elem_id="layout_result")
            
        apply_btn.click(
            apply_layout, 
            inputs=[font_size, line_mode, line_height], 
            outputs=[layout_result, style_box])
            
        process_btn.click(
            process_file,
            inputs= upload,
            outputs=ocr_box,
        )
        
        clean_btn.click(
            clean_ocr_result,
            inputs= None,
            outputs=edit_box,
        )

    gr.Markdown("---")
    
    gr.HTML(
        """
        <style>
        
            /* Always show a vertical scrollbar inside the textarea */
            #ocr_box textarea      { 
                border: none !important;
                box-shadow: none !important;
                outline: none !important;
                white-space: pre-wrap;
                }
                
            /* Repeat for the cleaned‑text editor, if desired */
            #edit_box textarea     { 
                border: none !important;
                box-shadow: none !important;
                outline: none !important;
                overflow-y: scroll !important; 
                overflow-x: hidden; 
                white-space: pre-wrap;}
                
            #layout_result textarea    { 
            border: none !important;
            box-shadow: none !important;
            outline: none !important;
            white-space: pre-wrap;}
            
            #font_size, #line_mode, #line_height {
            /* stack the options vertically instead of the default row layout */
            display: flex !important;
            flex-direction: column !important;
            gap: .75rem;                       /* space between rows */
            }
            
            /* ── Radio‑GROUP titles ─────────────────────────────────────────────── */
            #font_size   > label,
            #line_mode   > label,
            #line_height > label {
                font-weight: bold;      /* bold  */
                font-size:   30pt;     /* ≈16 px */
                color:       #1f2937;  /* Tailwind gray‑800 (dark grey) */
                margin-bottom: .25rem; /* little breathing room */
            }
            
            /* remove the grey pill‑shaped box around each <label> */
            #font_size label,
            #line_mode label,
            #line_height label {
                border: none !important;
                box-shadow: none !important;
                padding: 0 !important;
            }

            /* make the radio bullets bigger + black accent colour */
            #font_size input[type="radio"],
            #line_mode input[type="radio"],
            #line_height input[type="radio"] {
                width: 18px;
                height: 18px;
                accent-color: #000;                /* black fill for checked state */
            }

            /* optional: subtle divider line between the three groups */
            #font_size::after,
            #line_mode::after {
                content: "";
                display: block;
                height: 1px;
                background: #e5e5e5;
                margin: 1rem 0;
            }
            
        </style>
        """
    )

# Launch the interface
if __name__ == "__main__":
    demo.launch(share=True)
