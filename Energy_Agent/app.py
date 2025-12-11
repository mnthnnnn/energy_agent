from flask import Flask, render_template, request, Response
from agent import input_understanding, state_tracker, task_planner, output_generator, reset_state

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/stream", methods=["POST"])
def stream():
    user_text = request.form["user_text"]
    reset_state()
    cls = input_understanding(user_text)
    st_state = state_tracker(cls)
    plan = task_planner()

    def generate():
        for word in output_generator(plan, stream=True):
            yield word + " "

    return Response(generate(), mimetype="text/plain")

if __name__ == "__main__":
    app.run(debug=True)
