import warnings
warnings.simplefilter("ignore") # Slider List Extension is not supported

from container_manager import ContainerManager
import report_lib
import un_util #.slack()

# DL = DriveDownloader()

# This is currently being manually scripted
input = 'input/hella/Hella November 2021'
cm = ContainerManager(input)

old_manager = ContainerManager('input/hella/Hella Old')
cm.load_knowns(old_manager)

# report_lib.make_final_report(cm)
# report_lib.make_history_report(cm)
report_lib.make_unknown_report(cm)
report_lib.make_gap_report(cm, old_manager)
report_lib.make_new_report(cm, old_manager)
