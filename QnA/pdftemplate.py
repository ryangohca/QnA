from fpdf import FPDF

class WorksheetPDF(FPDF):
    
    def add_image(self, topx, topy, img_dir):
        # Note that topx, topy is in millimeters
        self.set_xy(topx, topy)
        self.image(img_dir)
        
