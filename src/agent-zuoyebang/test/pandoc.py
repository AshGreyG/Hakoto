import pypandoc

class Test :
    @staticmethod
    def math_symbol() -> None :
        math_markdown = r"""
由离心率 $e=\frac{c}{a}=\sqrt{3}$ 得 $c=\sqrt{3}a$，又 $c=2\sqrt{2}$，故 $a=\frac{2\sqrt{6}}{3}$，$b^2=c^2-a^2=\frac{16}{3}$。双曲线方程为 $\frac{9x^2}{32}-\frac{3y^2}{16}=1$。

设直线 $l: y=k(x-2\sqrt{2})$，与双曲线联立得：
$\frac{9x^2}{32}-\frac{3[k(x-2\sqrt{2})]^2}{16}=1$，整理得 $(9-6k^2)x^2+24\sqrt{2}k^2x-(48k^2+32)=0$。

设 $M(x_1,y_1)$, $N(x_2,y_2)$，由 $|FM|=5|FN|$ 得 $x_1-2\sqrt{2}=-5(x_2-2\sqrt{2})$，即 $x_1+5x_2=12\sqrt{2}$。由韦达定理 $x_1+x_2=-\frac{24\sqrt{2}k^2}{9-6k^2}$，$x_1x_2=-\frac{48k^2+32}{9-6k^2}$。

联立解得 $x_2=\frac{3\sqrt{2}(4k^2+3)}{9-6k^2}$，代入 $x_1=12\sqrt{2}-5x_2$ 后代入韦达定理得：
$12\sqrt{2}-4x_2=-\frac{24\sqrt{2}k^2}{9-6k^2}$，化简得 $16k^4-40k^2+9=0$。

解得 $k^2=\frac{5\pm\sqrt{7}}{4}$，即 $k=\pm\frac{\sqrt{5\pm\sqrt{7}}}{2}$。经检验，<strong style="color: red">当 $k^2=\frac{5+\sqrt{7}}{4}$ 时满足 $\Delta>0$</strong>，故 $k=\pm\frac{\sqrt{5+\sqrt{7}}}{2}$。
"""
        result = pypandoc.convert_text(
            math_markdown,
            to = "html",
            format = "markdown",
            extra_args = ["--mathjax"]
        )

        print(result)

if __name__ == "__main__" :
    Test.math_symbol()