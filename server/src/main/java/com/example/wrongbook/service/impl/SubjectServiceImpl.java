package com.example.wrongbook.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.wrongbook.common.BizException;
import com.example.wrongbook.dto.SubjectRequest;
import com.example.wrongbook.entity.Subject;
import com.example.wrongbook.mapper.SubjectMapper;
import com.example.wrongbook.service.SubjectService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class SubjectServiceImpl implements SubjectService {

    private final SubjectMapper subjectMapper;

    @Override
    public List<Subject> list() {
        return subjectMapper.selectList(new LambdaQueryWrapper<Subject>().orderByAsc(Subject::getSort));
    }

    @Override
    public Long add(SubjectRequest request) {
        Long count = subjectMapper.selectCount(
                new LambdaQueryWrapper<Subject>().eq(Subject::getName, request.getName()));
        if (count > 0) {
            throw new BizException("科目名称已存在");
        }
        Subject subject = new Subject();
        subject.setName(request.getName());
        subject.setCode(request.getCode());
        subject.setSort(request.getSort() == null ? 0 : request.getSort());
        subjectMapper.insert(subject);
        return subject.getId();
    }

    @Override
    public void update(Long id, SubjectRequest request) {
        Subject exist = subjectMapper.selectById(id);
        if (exist == null) {
            throw new BizException("科目不存在");
        }
        Subject subject = new Subject();
        subject.setId(id);
        subject.setName(request.getName());
        subject.setCode(request.getCode());
        subject.setSort(request.getSort());
        subjectMapper.updateById(subject);
    }
}
