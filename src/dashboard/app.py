import logging
from pathlib import Path

import pandas as pd
from flask import Flask, render_template_string, request

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "processed"
POSTS_PATH = DATA_DIR / "posts.csv"
COMMENTS_PATH = DATA_DIR / "comments.csv"

app = Flask(__name__)
logger = logging.getLogger(__name__)

HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Reddit Data Analytics Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root {
      --bg: #f8f9fa;
      --card: #ffffff;
      --text: #202124;
      --muted: #5f6368;
      --border: #dadce0;
      --accent: #1a73e8;
      --accent-soft: #e8f0fe;
      --radius: 14px;
      --shadow: 0 1px 2px rgba(60,64,67,.15), 0 1px 3px 1px rgba(60,64,67,.1);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
    }
    .container {
      max-width: 1240px;
      margin: 0 auto;
      padding: 24px 18px 40px;
    }
    h1 {
      margin: 0;
      font-size: 30px;
      font-weight: 600;
      letter-spacing: .1px;
    }
    .subtitle {
      color: var(--muted);
      margin: 8px 0 18px;
    }
    .filter-panel {
      background: var(--card);
      border: 1px solid var(--border);
      box-shadow: var(--shadow);
      border-radius: var(--radius);
      padding: 16px;
      margin-bottom: 16px;
    }
    form { display: flex; gap: 12px; align-items: flex-end; flex-wrap: wrap; }
    label { font-size: 13px; color: var(--muted); display: block; margin-bottom: 6px; }
    select {
      min-width: 280px;
      min-height: 120px;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 8px;
      background: #fff;
      color: var(--text);
    }
    button {
      border: 1px solid var(--accent);
      background: var(--accent);
      color: #fff;
      border-radius: 999px;
      padding: 10px 18px;
      cursor: pointer;
      font-weight: 600;
    }
    .cards {
      display: grid;
      grid-template-columns: repeat(6, minmax(130px, 1fr));
      gap: 12px;
      margin: 14px 0 18px;
    }
    .card {
      background: var(--card);
      border: 1px solid var(--border);
      box-shadow: var(--shadow);
      border-radius: var(--radius);
      padding: 14px;
    }
    .card .label { color: var(--muted); font-size: 12px; }
    .card .value { font-size: 24px; margin-top: 6px; font-weight: 600; }
    .grid-2 {
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 14px;
      margin-bottom: 14px;
    }
    .panel {
      background: var(--card);
      border: 1px solid var(--border);
      box-shadow: var(--shadow);
      border-radius: var(--radius);
      padding: 16px;
    }
    .panel h3 { margin: 0 0 12px; font-size: 17px; }
    .chart-lg { height: 320px; }
    .chart-sm { height: 320px; }
    .table-box { overflow-x:auto; }
    table { border-collapse: collapse; width: 100%; font-size: 14px; }
    th, td { border-bottom: 1px solid #edf0f2; padding: 10px; text-align: left; vertical-align: top; }
    th { color: var(--muted); font-weight: 600; background: #fbfcff; }
    .hint {
      font-size: 12px;
      color: var(--muted);
      background: var(--accent-soft);
      border-radius: 10px;
      padding: 8px 10px;
      margin-bottom: 12px;
    }
    @media (max-width: 1060px) {
      .cards { grid-template-columns: repeat(3, minmax(120px, 1fr)); }
      .grid-2 { grid-template-columns: 1fr; }
      .chart-lg, .chart-sm { height: 280px; }
    }
    @media (max-width: 640px) {
      .cards { grid-template-columns: repeat(2, minmax(110px, 1fr)); }
      h1 { font-size: 24px; }
    }
  </style>
</head>
<body>
  <main class="container">
    <h1>Reddit Data Analytics</h1>
    <p class="subtitle">Clean and simple dashboard from <code>data/processed/posts.csv</code> and <code>comments.csv</code>.</p>

    <section class="filter-panel">
      <form method="get">
        <div>
          <label for="subreddits"><b>Filter subreddits</b></label>
          <select id="subreddits" name="subreddit" multiple>
            {% for s in all_subreddits %}
            <option value="{{ s }}" {% if s in selected_subreddits %}selected{% endif %}>{{ s }}</option>
            {% endfor %}
          </select>
        </div>
        <button type="submit">Apply</button>
      </form>
    </section>

    <section class="cards">
      <div class="card"><div class="label">Total Posts</div><div class="value">{{ metrics.post_count }}</div></div>
      <div class="card"><div class="label">Total Comments</div><div class="value">{{ metrics.comment_count }}</div></div>
      <div class="card"><div class="label">Avg Post Score</div><div class="value">{{ metrics.avg_score }}</div></div>
      <div class="card"><div class="label">Comment / Post</div><div class="value">{{ metrics.comment_per_post }}</div></div>
      <div class="card"><div class="label">Active Subreddits</div><div class="value">{{ metrics.active_subreddits }}</div></div>
      <div class="card"><div class="label">Top Subreddit</div><div class="value">{{ metrics.top_subreddit }}</div></div>
    </section>

    <section class="grid-2">
      <div class="panel">
        <h3>Daily Activity Trend</h3>
        <div class="hint">Posts and comments over time for selected subreddits.</div>
        <div class="chart-lg"><canvas id="trendChart"></canvas></div>
      </div>
      <div class="panel">
        <h3>Top Subreddits by Posts</h3>
        <div class="chart-sm"><canvas id="subredditChart"></canvas></div>
      </div>
    </section>

    <section class="panel table-box">
      <h3>Top posts by score</h3>
      {{ table_html|safe }}
    </section>
  </main>

  <script>
    const trendLabels = {{ trend_labels|tojson }};
    const trendPostValues = {{ trend_post_values|tojson }};
    const trendCommentValues = {{ trend_comment_values|tojson }};
    const subredditLabels = {{ subreddit_labels|tojson }};
    const subredditValues = {{ subreddit_values|tojson }};

    new Chart(document.getElementById('trendChart'), {
      type: 'line',
      data: {
        labels: trendLabels,
        datasets: [
          { label: 'Posts', data: trendPostValues, borderColor: '#1a73e8', backgroundColor: 'rgba(26,115,232,0.14)', tension: 0.25, fill: true },
          { label: 'Comments', data: trendCommentValues, borderColor: '#34a853', backgroundColor: 'rgba(52,168,83,0.12)', tension: 0.25, fill: true }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom' } },
      }
    });

    new Chart(document.getElementById('subredditChart'), {
      type: 'bar',
      data: {
        labels: subredditLabels,
        datasets: [{ label: 'Posts', data: subredditValues, backgroundColor: '#1a73e8' }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } }
      }
    });
  </script>
</body>
</html>
"""


def _safe_series(df: pd.DataFrame, column: str, df_name: str, default=0) -> pd.Series:
    if column not in df.columns:
        logger.warning(
            "Column '%s' missing in %s DataFrame; using default values.",
            column,
            df_name,
        )
        return pd.Series([default] * len(df), index=df.index)
    return df[column]


def _normalized_subreddits(posts_df: pd.DataFrame) -> list[str]:
    subreddit_clean = posts_df["subreddit"].dropna().astype(str).str.strip()
    subreddit_clean = subreddit_clean.replace("", pd.NA).dropna()
    return sorted(subreddit_clean.unique().tolist())


def _filter_by_subreddits(df: pd.DataFrame, selected_subreddits: list[str], df_name: str) -> pd.DataFrame:
    if "subreddit" not in df.columns:
        logger.warning(
            "Column 'subreddit' missing in %s DataFrame; returning empty view.",
            df_name,
        )
        return df.head(0)
    if not selected_subreddits:
        return df.head(0)
    return df[df["subreddit"].isin(selected_subreddits)]


def _load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not POSTS_PATH.exists() or not COMMENTS_PATH.exists():
        raise FileNotFoundError(
            "Missing processed CSV files. Run `python src/main.py` first to generate data."
        )

    posts = pd.read_csv(POSTS_PATH)
    comments = pd.read_csv(COMMENTS_PATH)

    if "created_utc" not in posts.columns:
        posts["created_utc"] = pd.NaT
    if "created_utc" not in comments.columns:
        comments["created_utc"] = pd.NaT

    if "subreddit" not in posts.columns:
        posts["subreddit"] = "unknown"
    if "subreddit" not in comments.columns:
        comments["subreddit"] = "unknown"

    posts["created_utc"] = pd.to_datetime(posts["created_utc"], errors="coerce")
    comments["created_utc"] = pd.to_datetime(comments["created_utc"], errors="coerce")
    posts["date"] = posts["created_utc"].dt.strftime("%Y-%m-%d")
    comments["date"] = comments["created_utc"].dt.strftime("%Y-%m-%d")
    return posts, comments


@app.route("/")
def dashboard():
    posts, comments = _load_data()

    all_subreddits = _normalized_subreddits(posts)
    selected_subreddits = request.args.getlist("subreddit") or all_subreddits

    posts_view = _filter_by_subreddits(posts, selected_subreddits, "posts")
    comments_view = _filter_by_subreddits(comments, selected_subreddits, "comments")

    score_series = pd.to_numeric(_safe_series(posts_view, "score", "posts"), errors="coerce")
    post_count = len(posts_view)
    comment_count = len(comments_view)
    avg_score = round(score_series.mean(), 2) if post_count else 0
    comment_per_post = round(comment_count / post_count, 2) if post_count else 0
    active_subreddits = posts_view["subreddit"].nunique() if post_count else 0

    top_subreddit = "-"
    if post_count:
        top_subreddit_value = posts_view["subreddit"].value_counts().head(1)
        top_subreddit = top_subreddit_value.index[0] if not top_subreddit_value.empty else "-"

    posts_daily = posts_view.groupby("date", dropna=False).size().reset_index(name="posts")
    comments_daily = comments_view.groupby("date", dropna=False).size().reset_index(name="comments")
    trend = posts_daily.merge(comments_daily, on="date", how="outer").fillna(0)
    trend = trend[trend["date"].notna()].sort_values("date")

    subreddit_posts = (
        posts_view.groupby("subreddit", dropna=False)
        .size()
        .reset_index(name="posts")
        .sort_values("posts", ascending=False)
        .head(8)
    )

    top_posts = posts_view.sort_values("score", ascending=False).head(20) if "score" in posts_view.columns else posts_view.head(20)
    cols = [c for c in ["title", "subreddit", "score", "num_comments", "created_utc", "url"] if c in top_posts.columns]
    table_html = top_posts[cols].to_html(index=False, classes="table") if len(top_posts) and cols else "<p>No data.</p>"

    return render_template_string(
        HTML_TEMPLATE,
        all_subreddits=all_subreddits,
        selected_subreddits=selected_subreddits,
        metrics={
            "post_count": f"{post_count:,}",
            "comment_count": f"{comment_count:,}",
            "avg_score": avg_score,
            "comment_per_post": comment_per_post,
            "active_subreddits": f"{active_subreddits:,}",
            "top_subreddit": top_subreddit,
        },
        trend_labels=trend["date"].tolist(),
        trend_post_values=trend["posts"].astype(int).tolist(),
        trend_comment_values=trend["comments"].astype(int).tolist(),
        subreddit_labels=subreddit_posts["subreddit"].astype(str).tolist(),
        subreddit_values=subreddit_posts["posts"].astype(int).tolist(),
        table_html=table_html,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8501, debug=False)
