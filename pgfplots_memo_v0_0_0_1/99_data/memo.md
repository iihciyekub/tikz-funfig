
<!--转换为分母格式-->
/pgf/number format/frac
<!--小数点位数-->
/pgf/number format/precision=2
<!--不足补0-->
/pgf/number format/fixed,    
<!--使用fixed方法四舍五入-->
/pgf/number format/fixed zerofill
<!--格式化文本,科学计算法-->
/pgf/number format/sci
<!--打印轴数值刻度-->
\pgfmathprintnumber{\tick}


\pgfkeysvalueof{/pgfplots/xmin}
\pgfkeysvalueof{/data point/meta}
\pgfkeysvalueof{/data point/x}
\pgfkeysvalueof{/data point/index}  == \coordindex

\NewDocumentCommand\calxy{r()}{%
    \footnotesize
    \pgfplotspointgetcoordinates{(#1)}%
    (\pgfmathprintnumber[/pgf/number format/precision=2]{\pgfkeysvalueof{/data point/x}},%
    \pgfmathprintnumber[/pgf/number format/precision=2]{\pgfkeysvalueof{/data point/y}})
}






<!--获取轴刻度索引0,1,2,3,...-->
\ticknum
<!--获取轴刻度数值-->
\tick
<!--获取下一个轴刻度数值-->
\pgfmathprintnumber{\nexttick}







<!--字体命令-->
\bfseries


