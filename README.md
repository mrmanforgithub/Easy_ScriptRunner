## 简单的用于游戏的图像识别脚本编辑器
这东西没啥含金量，我拿来打游戏日常的，你别说还确实能用（）<br>
唯一的好处可能是···不用写对应游戏的专属代码？只需要截截图就能运行，适合小白一点。<br>
在我的一代基础上，把界面改的好看了一些，并且优化了一些体验和构筑，比起原本的屎山代码来说，现在至少好了一些<br>


## 介绍
![1fa3240f1969a7d7762e36e0e5f0e7ce](https://github.com/mrmanforgithub/Easy_ScriptRunner/assets/98746422/2b245723-ce4a-4fd4-accd-30dc69301c58)
这是个基于图片识别的Python程序，因为作者我的代码能力非常垃圾，所以基本上是让gpt帮我写的，bug很多，功能也很不完善。<br>
但是如果是一些简单的操作，这程序还真有点用？（存疑）<br>
它可以在识别特定图片成功后执行模拟鼠标点击、滚轮滚动、键盘输入等操作，我写这个是为了帮我打游戏的每日日常，也打算让它帮我刷边狱巴士的地牢。<br>
可恶，但是完全没法成功，目前帮我打完一场战斗就不错了，自动寻路更是做不出来，晕倒。。。。<br>

## 安装
我觉得克隆这个可能要导的包很大（不知道是不是我导的包太多了的问题···），所以其实黏贴代码到pycharm这种集成式开发软件中，让软件帮你导包，然后运行就行了，所以我就不写requirement.txt了 ，毕竟我觉得都上github了，应该也是自己在打代码的···吧？<br>

## 使用
1.在pycharm里运行。开启main.py后会自动帮你创一个新扫描<br><br>
2.出来的图形界面中输入图片的位置（也可以用我这个软件来截图，点手动框选/一键截图就好  会在桌面上框一个位置（点了后屏幕会变白，然后会有框框出现，和普通截图没啥差别）<br><br>
3.然后去事件里添加如果扫描到了，希望发生的事件（比如鼠标键盘操作啊）<br><br>
4.菜单栏里点保存全局文件，方便下次打开捏<br><br>
5.然后点开始扫描就行了<br><br>
6.下一次要用，直加载全局文件，会帮你自动把脚本和操作都导入进去，有几个扫描页面同时出现，这里就都会被一起创建出来。<br><br>
7.快捷键是f1，按下全部统一开始扫描，esc按下全部停止扫描（有几率出bug不生效）<br><br>
8.建议一次不要开多个脚本一起扫描，会卡，虽然对游戏没啥影响，但是这个脚本运行器会卡<br><br>

## 案例
我以打地鼠这个游戏为例吧<br><br>
截一张老鼠的图片，开新的扫描，导入图片，框选打地鼠游戏页面对应的位置（记得点记录位置，不然是不算的哦）。<br><br>
然后点开事件页面，在新窗口中把默认的那几个操作删掉，添加新的操作为 自动寻路，输入xy均为0（意思就是在识别到的图片位置产生一次鼠标点击）<br><br>
点击开始扫描，然后你就可以看到脚本帮你自动打地鼠，非常nice。<br><br>

## 注意
操作列表里有开始扫描和关闭扫描两个特殊的选项，建议不要一次开启太多扫描<br><br>
扫描开启多个，界面会开始卡顿。如果真的需要很多扫描，请使用界面右侧那一堆图标中的播放按钮，那个按钮是循环扫描按钮，使用那个不怎么会引起卡顿<br><br>