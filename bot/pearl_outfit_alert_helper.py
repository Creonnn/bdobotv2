
def format_pearl_alert(outfits):
    deliverable = "There are outfits sitting right now!\n\n"
    for outfit, quantity in outfits.items():
        deliverable += f"{outfit} x{quantity}\n"
    return deliverable

if __name__ == '__main__':
    pass