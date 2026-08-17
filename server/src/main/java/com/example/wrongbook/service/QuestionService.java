package com.example.wrongbook.service;

import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.example.wrongbook.dto.QuestionRequest;
import com.example.wrongbook.entity.Question;
import jakarta.servlet.http.HttpServletResponse;

public interface QuestionService {

    /** 录入错题（当前登录学生），返回错题 ID */
    Long create(QuestionRequest request);

    /** 错题分页筛选（学生强制本人数据，按科目/知识点） */
    Page<Question> page(Integer pageNum, Integer pageSize, Long subjectId, Long knowledgePointId);

    /** 错题详情（学生仅本人） */
    Question detail(Long id);

    /** 修改错题（学生仅本人） */
    void update(Long id, QuestionRequest request);

    /** 删除错题（学生仅本人，逻辑删除并级联清理解析/变式题/复习计划） */
    void remove(Long id);

    /** 导出错题本（.xlsx，按科目/知识点筛选，写入响应流） */
    void export(Long subjectId, Long knowledgePointId, HttpServletResponse response);
}
