from fpdf import FPDF

class WorksheetPDF(FPDF):
    
    def add_image(self, topx, topy, img_dir):
        self.set_xy(topx, topy)
        self.image(img_dir)
        
