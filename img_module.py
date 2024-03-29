from PIL import Image
from PIL import ImageFilter
from PIL import ImageEnhance
from PIL import ImageDraw
import numpy as np
import matplotlib.pyplot as plt
from icrawler.builtin import GoogleImageCrawler
import ocr_module
import txt_module


threshold = 100		#2値化するしきい値 経験的に50あたりが文字の印字部分
threshold_half_up = 100	#領域抽出後の2値化のしきい値

#2値化の画素値の指定用定数
IMAGE_BLACK = 0
IMAGE_WHITE = 255

#指定回数膨張させる(白領域を増やす)
def img_opening(img, n):
	img_op = img
	for i in range(n):
		img_op = img_op.filter(ImageFilter.MaxFilter())
	return img_op

#指定回数縮小させる(黒領域を増やす)
def img_closing(img, n):
	img_cl = img
	for i in range(n):
		img_cl = img_cl.filter(ImageFilter.MinFilter())
	return img_cl

#グレースケールを表示する処理
def img_to_gray(target):
	img = Image.open(target)
	gray_img = img.convert("L")
	gray_img.show()

#画像のヒストグラムを表示する処理
def show_img_histogram(img):
	plt.plot(img.histogram())
	plt.show()

#OCRの結果配列から画像を特定のディレクトリに保存する処理
def get_img_result_word(list):
	txt = get_maxlen_content(list)
	detect_word = txt_module.revision_txt(txt)
	crawler = GoogleImageCrawler(storage={"root_dir" : "get_result"})
	crawler.crawl(keyword=detect_word, max_num=3)

#
def ticket_threshold(target):
	img = Image.open(target)
	gray_img = img.convert("L")

	gray_img = gray_img.resize( (int(gray_img.width / 2), int(gray_img.height / 2) ) )

	#ラムダ式で2値化 画像は0(黒)～255(白)
	#黒が濃い(文字の印字)部分を残し、それ以外を白く飛ばす
	#経験的にヒストグラムでは文字の画素は50くらいが多い
	bin_img = gray_img.point(lambda x: IMAGE_BLACK if x < threshold else IMAGE_WHITE)
	#show_img_histogram(gray_img)

	pre_img = bin_img

	rem_noise_img = pre_img

	rem_noise_img = img_cut_half_up(rem_noise_img)

	rem_noise_img = rem_noise_img.convert("RGB")

	pos = ocr_module.target_to_ocr(rem_noise_img)

	#rem_noise_img.show()

	#ブラウザに一旦、切り出した画像を返す → タイトル領域を選ばせる

	area_point_arr = []
	cnt = 0;

	for iter in pos:
		#抽出文字列長が短いときはノイズとして除外する
		if len(iter.content) > 5:
			x_st = iter.position[0][0]
			y_st = iter.position[0][1]
			x_en = iter.position[1][0]
			y_en = iter.position[1][1]
			im_cut = rem_noise_img.crop((x_st, y_st, x_en, y_en))
			img_name = "./area/" + str(cnt) + ".jpg"
			im_cut.save(img_name)
			print(cnt, ":" ,iter.content)

			cnt = cnt + 1
			area_point_arr.append([x_st, y_st, x_en, y_en])


	#if len(area_point_arr) < 1:
	if len(pos) < 1:
		print("抽出できません")
		exit()

	return area_point_arr

#取得した領域に対してOCRする処理
def area_img_to_ocr(target, position):

	bin_img = img_proc_binary(target)
	bin_img = bin_img.crop(position)
	#bin_img.show()

	detect_list = ocr_module.test_trained_ocr(bin_img)

	get_img_result_word(detect_list)

#タイトル領域に対してOCRして結果を取得する処理 (debug用)
def title_area_ocr_wrapper(img):
	pos = ocr_module.target_to_ocr(img)

	if len(pos) < 1:
		print("抽出できません")
		exit()

	for iter in pos:
		print(iter.content)

#画像の上半分を切り出す関数
def img_cut_half_up(img):
	return img.crop((0, 0, img.width, int(img.height / 2) ))

#対象を上半分の2値画像に切り出す処理
def img_proc_binary(target):
	img = Image.open(target)
	gray_img = img.convert("L")
	gray_img = gray_img.resize( (int(gray_img.width / 2), int(gray_img.height / 2) ) )
	gray_img = img_cut_half_up(gray_img)

	bin_img = gray_img.point(lambda x: IMAGE_BLACK if x < threshold_half_up else IMAGE_WHITE)

	#bin_img = img_closing(bin_img, 1)
	#bin_img = img_opening(bin_img, 1)

	#show_img_histogram(bin_img)

	return bin_img

#最大の文字列の抽出結果を取得する処理
def get_maxlen_content(list):
	result = ""
	if len(list) > 1:
		result = list[0].content
		for i in range(1, len(list), 1):
			if len(result) < len(list[i].content):
				result = list[i].content
	else:
		result = list[0].content
	return result

#各学習済の元の学習データでOCRする処理(debug用)
def test_default_model(target):
	gray_img = img_proc_filter(target)
	gray_img.show()

	ocr_module.test_default_model_ocr(gray_img)

#数種類のモデルで識別する処理(debug用)
def test_trained_model(target):
	gray_img = img_proc_filter(target)

	gray_img.show()

	detect_list = ocr_module.test_trained_ocr(gray_img)

	for i in detect_list:
		txt_module.print_detect_word(i.content)

	get_img_result_word(detect_list)

#タイトル領域に画像を切り出す(debug用)
def cut_title_area(target, position):
	bin_img = img_proc_binary(target)
	bin_img = bin_img.crop(position)

	bin_img.show()
	bin_img.save("./tmp.jpg")

#指定した画像にフィルタをかける処理
def img_proc_filter(target):
	img = Image.open(target)
	gray_img = img.convert("L")

	#pos_img = ImageDraw.Draw(gray_img)
	#pos_img.rectangle((0, 0, gray_img.width, gray_img.height))

	gray_img = gray_img.resize( (int(gray_img.width * 1.2), int(gray_img.height * 1.2) ) )
	#gray_img = gray_img.resize( (500, 100 ) )
	gray_img = gray_img.filter(ImageFilter.MedianFilter())

	#sharp = ImageEnhance.Sharpness(gray_img)
	#sharp.enhance(2.0)

	#gray_img = img_closing(gray_img, 2)
	#gray_img = img_opening(gray_img, 1)

	#gray_img = gray_img.filter(ImageFilter.GaussianBlur(0.5))

	result = gray_img
	return result
