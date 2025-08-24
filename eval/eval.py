import json, time, requests

API = "http://127.0.0.1:8000/chat"
DATA = "eval/qa.jsonl"

def ask(q):
    payload = {"user_id": "eval", "message": q, "grounded_only": True}
    r = requests.post(API, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()

def score(answer: str, keywords):
    ans = answer.lower()
    hits = sum(1 for k in keywords if k.lower() in ans)
    return hits, len(keywords)

def run():
    total = 0
    ok_kw = 0
    ok_src = 0
    with open(DATA, "r", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            q = item["question"]
            kws = item["keywords"]
            must = item.get("must_source")

            res = ask(q)
            reply = res.get("reply","")
            sources = res.get("sources") or []

            h, n = score(reply, kws)
            total += 1
            if h == n: ok_kw += 1
            if must and must in sources: ok_src += 1

            print(f"Q: {q}")
            print(f"A: {reply}")
            print(f"Keywords: {h}/{n}  Sources OK: {must in sources}")
            print("-"*60)
            time.sleep(0.3)

    print("== Summary ==")
    print(f"Keyword coverage: {ok_kw}/{total}")
    print(f"Source correctness: {ok_src}/{total}")

if __name__ == "__main__":
    run()
