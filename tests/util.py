def hasattrnested(obj: object, attr: str):
    if "." in attr:
        parent, child = attr.split(".", 1)
        return hasattr(obj, parent) and hasattrnested(getattr(obj, parent), child)
    else:
        return hasattr(obj, attr)
