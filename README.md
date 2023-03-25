# gift-wrapper

This is Python software to easily build [GIFT](https://docs.moodle.org/en/GIFT_format) -based [question banks](https://docs.moodle.org/en/Question_bank) in [Moodle](https://moodle.org/). Other similar tools are available (you can search for *Tools that create or process GIFTs* in [Moodle's GIFT page](https://docs.moodle.org/en/GIFT_format)) but none of them fitted well my workflow. What I need is (the goals of `gift-wrapper` are):

* to write questions in plain text, and as many as I like in a single file
* to write latex formulas directly
* to easily/seamlessly include images

The most interesting point is probably the last one.

## Requirements

Python requirements are:

- Python &#8805; 3.10
- [paramiko](http://www.paramiko.org/)
- [colorama](https://pypi.org/project/colorama/)
- [pyyaml](https://pypi.org/project/PyYAML/)
- [tqdm](https://github.com/tqdm/tqdm)

Now, if you want to make the most of the software you also need:

* [pdflatex](https://en.wikipedia.org/wiki/PdfTeX) (i.e. a [TeX](https://en.wikipedia.org/wiki/TeX) distribution)
* [pdf2svg](https://github.com/dawbarton/pdf2svg/)
* disk space in a remote server that can host your images

## Install

```
pip install gift-wrapper
```

should suffice.

### Manual setup

If you rather clone this repository, (in order to, potentially, get the latest additions/modifications)  

```
pip install pyyaml paramiko tqdm colorama
```

should install all the additional requirements. If you use [Anaconda](https://anaconda.org/), the [bash](https://en.wikipedia.org/wiki/Bash_%28Unix_shell%29) script `make_conda_environment.sh` will make a proper environment (named `gift`).

After that, you should be able to run the program.

## Usage

The main program is `wrap.py` and you can check the available command-line options with
```
wrap.py -h
```
or
```
python wrap.py -h
```
if you did a manual installation and `wrap.py` doesn't have execution permissions. 

If you don't pass any argument, `parameters.yaml` and `bank.yaml` files are expected. The former is a settings file whereas the latter is the actual *input file* in which you must write the questions.

The output will be a text file in GIFT format with the same name as the input (the file with the questions) but `.gift.txt` extension (thus, `bank.gift.txt`, by default). It seems that *sometimes* Moodle has troubles importing (recognizing) a text file if the extension is not `.txt`. 

### Parameters

`parameters.yaml` is a [YAML](https://en.wikipedia.org/wiki/YAML) file intended to hold settings that you only need to specify once. Right now, it only contains parameters related to `images hosting` (needed to copy your images to a remote server). All the options are either self-explanatory or explained through comments. It should be fairly easy to tweak the [included example](parameters.yaml) for your own setup.

### Questions

Questions are specified through another *YAML* file. The first parameter, `pictures base directory`, refers to the base directory that will be created in the remote host to accommodate your images (only meaningful if images are **not** embedded in the questions, i.e., if not passing `-e`). It is meant to separate different question banks (so that you can have, e.g., directories `quiz 1` and `quiz 2`). The rest of the file is a **list of categories**, and inside each one there is a **list of questions**. Hopefully, the format is clear from either the name of the settings and/or its companion comments. You are probably better off taking a look at the [provided example](bank.yaml).

### Example

If you run the program inside the `gift-wrapper` directory as is, it will process the sample `bank.yaml` which includes a `.tex`, a `.svg` and some mathematical formulas, and will generate a `bank.gift.txt` file which you can import from Moodle (choosing the GIFT format when asked). If the parameters file (by default, `parameters.yaml`) is not found, images are embedded into the corresponding questions (tantamount to passing `-e`).

## Including images

`gift-wrapper` has been designed to work with [svg](https://en.wikipedia.org/wiki/Scalable_Vector_Graphics) images. Then, in order to include any image in a question, two scenarios are contemplated:

* you already have an svg
* you have a TeX file **that can be compiled with *pdflatex***

In any case, you just need to write the path to the file inside the text of the question (whether in the `statement`, the `answer` or the `feedbak`). If in the second scenario, i.e., you are including a *TeX* file, this will be compiled into a pdf with *pdflatex*, and then converted to an svg with *pdf2svg*. Hence, a *svg* file will be, in the end, available for every image.

Images (*svg*s) are either copied to a remote host (and properly linked in the output GIFT file), or directly embedded into their corresponding questions.

Characters allowed in a path (to either a `.tex` or a `.svg`) are:
* alphanumeric (A-Z, a-z, 0-9)
* underscore, '_', and dash, '-'
* '/' and '\\' (path separators).

### Browser compatibility

It seems (it has been reported) not every browser properly handles svg images (maybe other types too) embedded in a question as an URL. My experience so far is both [Firefox](https://www.mozilla.org/en-US/firefox) and [Chromium](https://www.chromium.org/Home) (at the time of writing this) work just fine. 

### Do I really need pdf2svg?

Only if you want automatic conversion from `.tex` (passing through `.pdf`) to `.svg`, i.e., only if you embed a `.tex` somewhere.
Also, there is (probably) nothing special about *pdf2svg* and, in principle, you can use any command-line program that takes as arguments the input pdf and the output svg. However, I've only tested the program with *pdf2svg* since it's the one included in [Gentoo Linux](https://www.gentoo.org/).

## Remote access

If a parameters file (e.g., `parameters.yaml`) is found, images are by default copied to the specified remote host (within a publicly visible directory) so that they can be accessed by Moodle. This is done automatically for every embedded image (svg or tex). For this to work, in the `parameters.yaml` file, within `ssh` either

* user and password, or
* user and path to a public key file

(but **not both**) should be specified.

You can inhibit this behavior and run the program locally (omitting the transferring of the images to a remote host) by using `-l` command line argument. This is especially meaningful if you don't have any embedded image in your questions (and hence nothing needs to be copied to a remote host).

## Latex support

Formulas inside `$`s are processed and, within them, these are the commands/symbols that have been tested so far

- greek letters
- subindexes
- calligraphic symbols, i.e., prefixed by `\cal`
- fractions with `\frac{}{}`
- `\underline`
- `\left(` and `\right)`
- `\left[` and `\right]`
- `\begin{bmatrix}` and `\end{bmatrix}`
- symbols `\sim`, `\approx`

More things are probably OK, but I have not tested them yet.

Inside text, only commands `\textit` and `\textbf` are supported for the time being.

### Safety checks

By default, `wrap.py` checks whether or not the formulas you wrote between `$`'s can actually be compiled. Right now this involves a call to `pdflatex` *for every formula*, meaning that it can significantly slow down the process. It can be disabled by passing ` --no-checks` (or simply `-n`). It is probably a good idea to actually check the formulas every once in a while (e.g., every time you add a new one), though, since *bad* latex formulas will be (silently) imported by Moodle anyway, and not only will they be incorrectly rendered but they may also mess up subsequent content.  

## Current limitations

- only *numerical* and *multiple-choice* questions are supported (notice that the GIFT format itself doesn't support every type of question available in Moodle)

- the latex support is very basic

- one is in for troubles if embedding remote URLs pointing to `.svg` or `.tex` files since the file part will, most likely, be parsed and replaced

## See also

If you are comfortable with Python and [Jupyter](https://jupyter.org/) notebooks, you might also be interested in [py2gift](https://github.com/manuvazquez/py2gift).
