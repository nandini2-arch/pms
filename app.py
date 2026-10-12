import math
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request

app = Flask(__name__, template_folder=".")

TOTAL_SLOTS = 12
RATE_PER_HOUR = 20  # change this to set your price

# slot number -> {"plate": str, "since": datetime} or None
slots = {i: None for i in range(1, TOTAL_SLOTS + 1)}


@app.route("/")
def home():
    return render_template("index.html", rate=RATE_PER_HOUR)


@app.get("/api/slots")
def get_slots():
    return jsonify(
        [
            {
                "id": i,
                "plate": v["plate"] if v else None,
                "since": v["since"].isoformat() if v else None,
            }
            for i, v in slots.items()
        ]
    )


@app.post("/api/park")
def park():
    plate = (request.json.get("plate") or "").strip().upper()
    if not plate:
        return jsonify(error="Enter a vehicle number."), 400
    if any(v and v["plate"] == plate for v in slots.values()):
        return jsonify(error=f"{plate} is already parked."), 400
    free = next((i for i, v in slots.items() if v is None), None)
    if free is None:
        return jsonify(error="Parking is full."), 400
    slots[free] = {"plate": plate, "since": datetime.now(timezone.utc)}
    return jsonify(message=f"{plate} parked in bay {free}.")


@app.post("/api/release")
def release():
    slot = int(request.json.get("slot", 0))
    car = slots.get(slot)
    if not car:
        return jsonify(error="That bay is already empty."), 400
    seconds = (datetime.now(timezone.utc) - car["since"]).total_seconds()
    hours = max(1, math.ceil(seconds / 3600))  # minimum 1 hour
    fee = hours * RATE_PER_HOUR
    slots[slot] = None
    return jsonify(message=f"{car['plate']} left bay {slot}. {hours} hr billed. Fee: {fee}")


if __name__ == "__main__":
    app.run(debug=True)
