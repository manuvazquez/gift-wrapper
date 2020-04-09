# gift-wrapper

This is Python software to easily build [GIFT](https://docs.moodle.org/38/en/GIFT_format) -based [question banks](https://docs.moodle.org/38/en/Question_bank) in [Moodle](https://moodle.org/). Other similar tools are available (you can search for *Tools that create or process GIFTs* in [Moodle's GIFT page](https://docs.moodle.org/38/en/GIFT_format)) but none of them fitted well my workflow. What I need is (the goals of `gift-wrapper` are):

* to write questions in plain text, and as many as I like in a single file
* to write latex formulas directly
* to easily/seamlessly include images

The most interesting point is probably the last one.

## Requirements

Python requirements are:

- [paramiko](http://www.paramiko.org/)
- [colorama](https://pypi.org/project/colorama/)
- [pyyaml](https://pypi.org/project/PyYAML/)
- [tqdm](https://github.com/tqdm/tqdm)

If you use Anaconda, the [bash](https://en.wikipedia.org/wiki/Bash_%28Unix_shell%29) script `make_conda_environment.sh` will make a proper environment (named `gift`).

If you want to take advantage of the whole package you need:

* [pdflatex](https://en.wikipedia.org/wiki/PdfTeX)
* [pdf2svg](https://github.com/dawbarton/pdf2svg/)
* access to a remote (which is also public) for hosting the images

## Including images

`gift-wrapper` has been designed to work with [svg](https://en.wikipedia.org/wiki/Scalable_Vector_Graphics) images. Then, in order to include any image in a question, two scenarios are contemplated:

* you already have an svg
* you have a [TeX](https://en.wikipedia.org/wiki/TeX) file **that can be compiled with [pdflatex](https://en.wikipedia.org/wiki/PdfTeX)**

In any case, you just need to write the path to the file inside the text of the question (whether in the `statement`, the `answer` or the `feedbak`). If in the second scenario, i.e., you are including a *TeX* file, this will be compiled into a pdf with *pdflatex*, and then converted to a svg with [pdf2svg](https://github.com/dawbarton/pdf2svg/). Hence, in the end a *svg* file for every image is available.

Images (*svg*s) are then copied to a remote host, and properly linked in the output GIFT file.

### Do I need pdf2svg?

There is (probably) nothing special about *pdf2svg* and, in principle, you can use any command-line program that takes as arguments the input pdf and the output svg. However, I've only tested the program with the above program since it's the one included in [Gentoo](https://www.gentoo.org/) Linux.

## Remote access

Images should be copied into some remote host that is public so that it can be accessed by Moodle.

You can run the program locally, i.e., omitting the transferring of the images to a remote host by using `-l` command line argument.

## Current limitations

- only *numerical* and *multiple-choice* questions are supported (notice that the GIFT format itself doesn't support every type of question available in Moodle)

- the support of latex is very basic: only formulas inside `$`s are processed (no, e.g., `\textit` or `\textbf` inside the text)

- embedded paths to images are only parsed correctly when surrounded by things usually recognized as whitespace (" ", new line)