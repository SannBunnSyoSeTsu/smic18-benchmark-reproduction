"""Rebuild from final sources and retain visual review only for identical PNGs."""
import argparse,json
from schematic_common import ROOT,case_path,make_case,sha,write,now


def freeze(slot):
    case=case_path(slot);p=case/'schematic_audit.json';previous=json.loads(p.read_text())
    assert previous['status']=='passed' and not previous['render_review_pending']
    old_images={name:h for name,h in previous['artifacts'].items() if name.endswith('.png')}
    if slot in [3,4,10,12,13,16,41,44,49]:
        from schematics_core import TITLES,layout_for
        current=make_case(slot,TITLES[slot],layout_for(slot))
    elif slot in [2,14,20,22,23,24,31,45]:
        from schematics_mixed import CONFIG
        titles,layout,blocks=CONFIG[slot];current=make_case(slot,titles,layout,blocks)
    else:
        from schematics_analog import TITLES,LAYOUTS
        current=make_case(slot,TITLES[slot],LAYOUTS[slot])
    new_images={name:h for name,h in current['artifacts'].items() if name.endswith('.png')}
    changed=[name for name in set(old_images)|set(new_images) if old_images.get(name)!=new_images.get(name)]
    current['final_source_freeze_at']=now()
    current['previous_visual_review']=dict(reviewed_at=previous['visual_reviewed_at'],note=previous['visual_review_note'],reviewed_png_hashes=old_images)
    current['rebuild_png_changes']=changed
    if not changed:
        current.update(status='passed',render_review_pending=False,all_pages_visually_reviewed=True,visual_reviewed_at=previous['visual_reviewed_at'],visual_review_note='All final sheet PNGs and full overview are byte-for-byte identical to the actually viewed artifacts; final renderer, symbols and layout sources were frozen beside the drawings.')
    write(p,current)
    print(json.dumps(dict(slot=slot,status=current['status'],sheets=current['sheets'],changed_images=changed),ensure_ascii=False),flush=True)
    return current


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('slots',nargs='+',type=int);args=p.parse_args()
    for slot in args.slots:freeze(slot)
