def screen_deal(data):
    ebitda = float(data["ebitda"]["value"].replace("$","").replace("M",""))

    if ebitda > 5:
        return "Go"
    return "No Go"