package com.example.wrongbook.vo;

import com.alibaba.excel.annotation.ExcelProperty;
import lombok.Data;

/**
 * 错题本导出行（EasyExcel）
 */
@Data
public class QuestionExportRow {

    @ExcelProperty("题干")
    private String stem;

    @ExcelProperty("答案")
    private String answer;

    @ExcelProperty("科目")
    private String subjectName;

    @ExcelProperty("知识点")
    private String knowledgePointName;

    @ExcelProperty("难度(1-5)")
    private Integer difficulty;

    @ExcelProperty("掌握度(0-100)")
    private Integer mastery;

    @ExcelProperty("来源")
    private String source;

    @ExcelProperty("录入时间")
    private String createTime;
}
