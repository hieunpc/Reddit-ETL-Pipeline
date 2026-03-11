from pathlib import Path

import pandas as pd
from flask import Flask, render_template_string, request

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "processed"
POSTS_PATH = DATA_DIR / "posts.csv"
COMMENTS_PATH = DATA_DIR / "comments.csv"

app = Flask(__name__)

HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Reddit ETL Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body { font-family: Arial, sans-serif; margin: 24px; background: #f8fafc; color: #111827; }
    h1 { margin-bottom: 8px; }
    .cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; }
    .card { background: white; padding: 16px; border-radius: 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.08); }
    .card .label { color: #6b7280; font-size: 13px; }
    .card .value { font-size: 26px; margin-top: 6px; }
    .charts { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }
    .chart-box { background: white; padding: 16px; border-radius: 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.08); }
    .table-box { background: white; padding: 16px; border-radius: 10px; box-shadow: 0 1px 2px rgba(0,0,0,0.08); overflow-x:auto; }
    table { border-collapse: collapse; width: 100%; font-size: 14px; }
    th, td { border-bottom: 1px solid #e5e7eb; padding: 8px; text-align: left; }
    th { background: #f3f4f6; }
    form { margin: 12px 0 20px; }
    select { min-width: 260px; min-height: 110px; }
  </style>
</head>
<body>
  <h1>📊 Reddit ETL Dashboard</h1>
  <p>Data source: <code>data/processed/posts.csv</code> and <code>comments.csv</code></p>

  <form method="get">
    <label for="subreddits"><b>Filter subreddits:</b></label><br/>
    <select id="subreddits" name="subreddit" multiple>
      {% for s in all_subreddits %}
      <option value="{{ s }}" {% if s in selected_subreddits %}selected{% endif %}>{{ s }}</option>
      {% endfor %}
    </select>
    <br/><br/>
    <button type="submit">Apply filter</button>
  </form>

  <div class="cards">
    <div class="card"><div class="label">Total Posts</div><div class="value">{{ metrics.post_count }}</div></div>
    <div class="card"><div class="label">Total Comments</div><div class="value">{{ metrics.comment_count }}</div></div>
    <div class="card"><div class="label">Avg Post Score</div><div class="value">{{ metrics.avg_score }}</div></div>
    <div class="card"><div class="label">Comment / Post</div><div class="value">{{ metrics.comment_per_post }}</div></div>
  </div>

  <div class="charts">
    <div class="chart-box">
      <h3>Posts per day</h3>
      <canvas id="postsChart"></canvas>
    </div>
    <div class="chart-box">
      <h3>Comments per day</h3>
      <canvas id="commentsChart"></canvas>
    </div>
  </div>

  <div class="table-box">
    <h3>Top posts by score</h3>
    {{ table_html|safe }}
  </div>

  <script>
    const postLabels = {{ post_labels|safe }};
    const postValues = {{ post_values|safe }};
    const commentLabels = {{ comment_labels|safe }};
    const commentValues = {{ comment_values|safe }};

    new Chart(document.getElementById('postsChart'), {
      type: 'line',
      data: { labels: postLabels, datasets: [{ label: 'Posts', data: postValues }] },
    });

    new Chart(document.getElementById('commentsChart'), {
      type: 'line',
      data: { labels: commentLabels, datasets: [{ label: 'Comments', data: commentValues }] },
    });
  </script>
</body>
</html>
"""


def _load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not POSTS_PATH.exists() or not COMMENTS_PATH.exists():
        raise FileNotFoundError(
            "Missing processed CSV files. Run `python src/main.py` first to generate data."
        )

    posts = pd.read_csv(POSTS_PATH)
    comments = pd.read_csv(COMMENTS_PATH)
    posts["created_utc"] = pd.to_datetime(posts["created_utc"], errors="coerce")
    comments["created_utc"] = pd.to_datetime(comments["created_utc"], errors="coerce")
    posts["date"] = posts["created_utc"].dt.strftime("%Y-%m-%d")
    comments["date"] = comments["created_utc"].dt.strftime("%Y-%m-%d")
    return posts, comments


@app.route("/")
def dashboard():
    posts, comments = _load_data()

    all_subreddits = sorted(posts["subreddit"].dropna().unique().tolist())
    selected_subreddits = request.args.getlist("subreddit") or all_subreddits

    posts_view = posts[posts["subreddit"].isin(selected_subreddits)]
    comments_view = comments[comments["subreddit"].isin(selected_subreddits)]

    post_count = len(posts_view)
    comment_count = len(comments_view)
    avg_score = round(posts_view["score"].mean(), 2) if post_count else 0
    comment_per_post = round(comment_count / post_count, 2) if post_count else 0

    posts_daily = posts_view.groupby("date").size().reset_index(name="count")
    comments_daily = comments_view.groupby("date").size().reset_index(name="count")

    top_posts = posts_view.sort_values("score", ascending=False).head(20)
    cols = [c for c in ["title", "subreddit", "score", "num_comments", "created_utc", "url"] if c in top_posts.columns]
    table_html = top_posts[cols].to_html(index=False, classes="table") if len(top_posts) else "<p>No data.</p>"

    return render_template_string(
        HTML_TEMPLATE,
        all_subreddits=all_subreddits,
        selected_subreddits=selected_subreddits,
        metrics={
            "post_count": f"{post_count:,}",
            "comment_count": f"{comment_count:,}",
            "avg_score": avg_score,
            "comment_per_post": comment_per_post,
        },
        post_labels=posts_daily["date"].tolist(),
        post_values=posts_daily["count"].tolist(),
        comment_labels=comments_daily["date"].tolist(),
        comment_values=comments_daily["count"].tolist(),
        table_html=table_html,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8501, debug=False)
