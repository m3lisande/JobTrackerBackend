# Bruno – JobTracker API

Use [Bruno](https://www.usebruno.com/) to test the JobTracker API.

## Setup

1. Install Bruno (desktop app or VS Code extension).
2. In Bruno: **Open Collection** → choose the `bruno` folder (this directory).
3. Select the **local** environment (dropdown top-right) so `base_url` = `http://localhost:5000`.
4. Start the backend: `poetry run python app.py`.

## Upload Resume

1. Open the **Upload Resume** request.
2. In the **Body** tab (Multipart Form):
   - **user_id**: keep `test-user-123` or set your user id.
   - **resume**: click **Select File** and choose a PDF (or any file).  
     If the editor shows `@file(/path/to/your/resume.pdf)`, replace that path with your actual file path, or use the UI to pick the file.
3. Send the request. You should get `201` with `{ "resume_key": "resumes/..." }`.

Use the returned `resume_key` in **POST /api/applications** as the `resume_key` field.
