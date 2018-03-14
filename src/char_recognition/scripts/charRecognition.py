import numpy
import cv2
import sys
from operator import itemgetter, attrgetter
from pattern_perceptor import PatternPerceptor
#sys.path.append('./faster_rcnn')
import time
import numpy as np

class CharRecognizer:
	def __init__(self):
		self.i = 0
		print "char_recognition module created!"
		self.pattern_perceptor = PatternPerceptor('/home/mj/datasets/ocr_data/train/deploy.prototxt', '/home/mj/datasets/ocr_data/train/numbers.caffemodel')
#	def find_location_of_characters(self, image):
#		print 'toooodooooo'

	def find_char_sequences(self, image, plates_location):
		char_list = list()
		croped_images = list()
		for plate in plates_location:
			plate_image = image[plate['y_begin']:plate['y_end'], plate['x_begin']:plate['x_end']]
#			cv2.imwrite('/home/mj/workspace/vehicle-registration-plate-recognition/plates/'+str(self.i)+'.jpg',plate_image)
#			self.i = self.i + 1
			plate_image = cv2.resize(plate_image,(370,83))
			bounding_rects = self.find_bounding_rects(plate_image)
			draw_image = plate_image.copy()
			for cnt in bounding_rects:
				x_begin = cnt['x_begin']
				y_begin = cnt['y_begin']
				x_end = cnt['x_end']
				y_end = cnt['y_end']
				cv2.rectangle(draw_image,(x_begin,y_begin),(x_end,y_end),(255,255,0),2)
#			cv2.imshow('draw', draw_image)
#			cv2.waitKey(20)
			if (len(bounding_rects) < 8):
				continue
#			print bounding_rects
			self.find_chars_type(bounding_rects, plate_image)
			char_list.append(bounding_rects)
			croped_images.append(cv2.resize(plate_image,(120,30)))
		return char_list , croped_images

	def find_chars_type(self, bounding_rects, croped_image):
		for cnt in bounding_rects:
			y_begin, y_end , x_begin , x_end = cnt['y_begin'],cnt['y_end'], cnt['x_begin'],cnt['x_end']
			char_image = croped_image[ y_begin:y_end, x_begin:x_end]
			char_type = self.pattern_perceptor.recognize(char_image)
			cnt['type'] = char_type

	def get_contours_bounding_rect(self, contours):
		bounding_rects = []
		for cnt in contours:
	        	x,y,w,h = cv2.boundingRect(cnt)
			bounding_rect = {'x_begin':x , 'y_begin':y, 'x_end':x+w, 'y_end':y+h , 'type':'nothing'}
			bounding_rects.append(bounding_rect)
		return bounding_rects

	def remove_abuse_contours(self, bounding_rects, w_max, image_width, image_height):
		selected_contours = []
		for i in range(len(bounding_rects)-1,-1,-1):
			cnt  = bounding_rects[i]
	        	w = cnt['x_end'] - cnt['x_begin']
	        	h = cnt['y_end'] - cnt['y_begin']
        		if( w < 10 or h < 10 or (w <30 and h < 20) or w > w_max):
				bounding_rects.pop(i)
                		continue
			if( cnt['x_begin'] < 5 or cnt['y_begin'] < 5 or cnt['x_end'] > image_width-5 or cnt['y_end']> image_height-5 or cnt['y_end'] < image_height/2):
				bounding_rects.pop(i)
				continue
		for i in range(len(bounding_rects)-1,-1,-1):
			contour_inside_numbers = 0
			cnt1  = bounding_rects[i]
			selected_j = 0
			for j in range(len(bounding_rects)-1,-1,-1):
				cnt2 = bounding_rects[j]
				if(cnt2['x_begin'] > cnt1['x_begin'] and cnt2['x_end'] < cnt1['x_end'] and cnt2['y_begin'] > cnt1['y_begin'] and cnt2['y_end'] < cnt1['y_end']):
					contour_inside_numbers = contour_inside_numbers + 1
					selected_j = j
			if(contour_inside_numbers == 1):
				bounding_rects.pop(selected_j)
			if(contour_inside_numbers > 1):
				aspect_ratio = float(cnt1['x_end'] - cnt1['x_begin'])/float(cnt1['y_end'] - cnt1['y_begin'])
				if(aspect_ratio > 0.5):
					bounding_rects.pop(i)
		selected_contours = bounding_rects
		return selected_contours	


	def find_bounding_rects(self, image):
		width_0 =  image.shape[1]
		height_0 = image.shape[0]
		gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
		start = time.time()
		kernel = np.ones((3,3),np.uint8)

		gray = cv2.erode(gray,kernel,iterations = 1)
		gray = cv2.dilate(gray,kernel,iterations = 1)
		gray = cv2.dilate(gray,kernel,iterations = 1)
		gray = cv2.erode(gray,kernel,iterations = 1)
		gray = cv2.erode(gray,kernel,iterations = 1)
		gray = cv2.dilate(gray,kernel,iterations = 1)
		gray = cv2.erode(gray,kernel,iterations = 1)

	#ret,thresh = cv2.threshold(gray,130,255,cv2.THRESH_BINARY_INV)
	#thresh = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,2)
	#thresh = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY,11,2)
	#thresh = cv2.threshold(gray,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)

	#	cv2.imshow('gray_open_closed' , gray)
		thresh = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY_INV,15,2)
#		thresh = cv2.erode(thresh,kernel,iterations = 1)
#		thresh = cv2.dilate(thresh,kernel,iterations = 1)
		__, contours, hierarchy = cv2.findContours(thresh.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
		if(len(contours) < 8):
			return list()
		bounding_rects = self.get_contours_bounding_rect(contours)
		bounding_rects = self.remove_abuse_contours(bounding_rects, thresh.shape[1]/2,thresh.shape[1],thresh.shape[0])
		if(len(contours) < 8):
			return list()
#		bounding_rects = bounding_rects.sort(key=lambda bounding_rects: bounding_rects.x_begin, reverse=False)
		return bounding_rects
