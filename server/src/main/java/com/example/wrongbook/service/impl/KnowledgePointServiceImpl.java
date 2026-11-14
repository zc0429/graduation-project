package com.example.wrongbook.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.wrongbook.common.BizException;
import com.example.wrongbook.common.ResultCode;
import com.example.wrongbook.dto.KnowledgePointRequest;
import com.example.wrongbook.entity.KnowledgePoint;
import com.example.wrongbook.entity.Subject;
import com.example.wrongbook.entity.Question;
import com.example.wrongbook.entity.AiAnalysis;
import com.example.wrongbook.entity.LearningContent;
import com.example.wrongbook.mapper.QuestionMapper;
import com.example.wrongbook.mapper.AiAnalysisMapper;
import com.example.wrongbook.mapper.LearningContentMapper;
import com.example.wrongbook.mapper.KnowledgePointMapper;
import com.example.wrongbook.mapper.SubjectMapper;
import com.example.wrongbook.service.KnowledgePointService;
import com.example.wrongbook.vo.KnowledgePointNode;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.BeanUtils;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class KnowledgePointServiceImpl implements KnowledgePointService {

    private final KnowledgePointMapper knowledgePointMapper;
    private final SubjectMapper subjectMapper;
    private final QuestionMapper questionMapper;
    private final AiAnalysisMapper aiAnalysisMapper;
    private final LearningContentMapper learningContentMapper;

    @Override
    public List<KnowledgePointNode> tree(Long subjectId) {
        LambdaQueryWrapper<KnowledgePoint> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(subjectId != null, KnowledgePoint::getSubjectId, subjectId)
                .orderByAsc(KnowledgePoint::getSort);
        List<KnowledgePoint> all = knowledgePointMapper.selectList(wrapper);
        Map<Long, List<KnowledgePoint>> byParent = all.stream()
                .collect(Collectors.groupingBy(KnowledgePoint::getParentId));
        List<KnowledgePointNode> roots = new ArrayList<>();
        for (KnowledgePoint kp : byParent.getOrDefault(0L, List.of())) {
            roots.add(toNode(kp, byParent));
        }
        return roots;
    }

    private KnowledgePointNode toNode(KnowledgePoint kp, Map<Long, List<KnowledgePoint>> byParent) {
        KnowledgePointNode node = new KnowledgePointNode();
        BeanUtils.copyProperties(kp, node);
        node.setChildren(byParent.getOrDefault(kp.getId(), List.of()).stream()
                .map(child -> toNode(child, byParent))
                .collect(Collectors.toList()));
        return node;
    }

    @Override
    public Long add(KnowledgePointRequest request) {
        Subject subject = subjectMapper.selectById(request.getSubjectId());
        if (subject == null) {
            throw new BizException("所属科目不存在");
        }
        if (request.getParentId() != 0) {
            KnowledgePoint parent = knowledgePointMapper.selectById(request.getParentId());
            if (parent == null || !parent.getSubjectId().equals(request.getSubjectId())) {
                throw new BizException("父级知识点不存在或不属于该科目");
            }
            if (!Long.valueOf(0).equals(parent.getParentId())) {
                throw new BizException("考点只能添加在一级章节下");
            }
        }
        KnowledgePoint kp = new KnowledgePoint();
        kp.setSubjectId(request.getSubjectId());
        kp.setParentId(request.getParentId());
        kp.setName(request.getName());
        kp.setSort(request.getSort() == null ? 0 : request.getSort());
        knowledgePointMapper.insert(kp);
        return kp.getId();
    }

    @Override
    public void remove(Long id) {
        KnowledgePoint kp = knowledgePointMapper.selectById(id);
        if (kp == null) {
            throw new BizException(ResultCode.NOT_FOUND.getCode(), "知识点不存在");
        }
        Long children = knowledgePointMapper.selectCount(
                new LambdaQueryWrapper<KnowledgePoint>().eq(KnowledgePoint::getParentId, id));
        if (children > 0) {
            throw new BizException("请先删除该章节下的考点");
        }
        if (questionMapper.selectCount(new LambdaQueryWrapper<Question>()
                .eq(Question::getKnowledgePointId, id)) > 0
                || aiAnalysisMapper.selectCount(new LambdaQueryWrapper<AiAnalysis>()
                .eq(AiAnalysis::getKnowledgePointId, id)) > 0
                || learningContentMapper.selectCount(new LambdaQueryWrapper<LearningContent>()
                .eq(LearningContent::getKnowledgePointId, id)) > 0) {
            throw new BizException("该知识点仍被错题或学习内容引用，不能删除");
        }
        knowledgePointMapper.deleteById(id);
    }
}
