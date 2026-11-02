package com.example.wrongbook.service;

import com.example.wrongbook.dto.SubjectRequest;
import com.example.wrongbook.entity.Subject;

import java.util.List;

public interface SubjectService {

    /** 科目列表（启用状态，按排序号） */
    List<Subject> list();

    /** 新增科目（管理员） */
    Long add(SubjectRequest request);

    /** 修改科目（管理员） */
    void update(Long id, SubjectRequest request);

    /** 删除科目：存在知识点或错题引用时拒绝删除 */
    void remove(Long id);
}
