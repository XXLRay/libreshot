import gtk

class Extended_Scrollbar(gtk.HScrollbar):
    __gtype_name__ = 'Extended_Scrollbar'
 
    def __init__(self):
        self.adjustedadjustment=gtk.Adjustment(0.0, 0.0, 201.0, 0.1, 1.0, 1.0)
        self.scalefactor=1.0
        self.offset=0
        super(Extended_Scrollbar,self).__init__(self.adjustedadjustment)
        
    def get_value(self):
        return ((super(Extended_Scrollbar,self).get_value()-self.offset)/self.scalefactor)

    def set_value(self,goto_pixel):
        super(Extended_Scrollbar,self).set_value(goto_pixel*self.scalefactor+self.offset)

    def set_range(self,gminimum,gmaximum):
        maxrange=65535
        if gmaximum<gminimum:
            swap=gmaximum
            gmaximum=gminimum
            gminimum=swap
        
        if gmaximum-gminimum>maxrange or gmaximum>32766 or gminimum<-32766:
            self.scalefactor=float(maxrange)/float(gmaximum-gminimum)
            gmaximum=32766
            gminimum=-32766
            self.offset=-32766
        else:
            self.scalefactor=1.0
            self.offset=0
        super(Extended_Scrollbar,self).set_range(gminimum,gmaximum)


    def get_adjustment(self):
        return super(Extended_Scrollbar,self).get_adjustment()  
    
    def set_adjustment_page_size(self,pagesize):
        super(Extended_Scrollbar,self).get_adjustment().set_page_size(pagesize*self.scalefactor)