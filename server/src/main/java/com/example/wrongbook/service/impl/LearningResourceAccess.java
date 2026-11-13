package com.example.wrongbook.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.example.wrongbook.common.BizException;
import com.example.wrongbook.common.ResultCode;
import com.example.wrongbook.common.UserContext;
import com.example.wrongbook.entity.PracticeRecord;
import com.example.wrongbook.entity.Question;
import com.example.wrongbook.entity.VariantQuestion;
import com.example.wrongbook.mapper.PracticeRecordMapper;
import com.example.wrongbook.mapper.QuestionMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.concurrent.locks.ReentrantLock;
import java.util.function.Supplier;

@Component
@RequiredArgsConstructor
public class LearningResourceAccess {
    private final QuestionMapper questionMapper;
    private final PracticeRecordMapper practiceRecordMapper;
    // Bounded single-instance single-flight locks; database writes still recheck snapshots.
    private final ReentrantLock[] locks = java.util.stream.IntStream.range(0, 64)
            .mapToObj(i -> new ReentrantLock()).toArray(ReentrantLock[]::new);

    public Question ownQuestion(Long id) {
        Question q = questionMapper.selectById(id);
        if (q == null) throw new BizException(ResultCode.NOT_FOUND.getCode(), "错题不存在");
        if (!"student".equals(UserContext.getRole()) || !q.getUserId().equals(UserContext.getUserId())) {
            throw new BizException(ResultCode.FORBIDDEN.getCode(), "无权访问该学习资源");
        }
        return q;
    }

    public <T> T serialized(Long id, Supplier<T> work) {
        ReentrantLock lock = locks[Math.floorMod(id.hashCode(), locks.length)];
        lock.lock();
        try { return work.get(); } finally { lock.unlock(); }
    }

    public boolean originalPracticed(Long questionId) {
        return practiceRecordMapper.selectCount(new LambdaQueryWrapper<PracticeRecord>()
                .eq(PracticeRecord::getUserId, UserContext.getUserId())
                .eq(PracticeRecord::getQuestionId, questionId)) > 0;
    }

    public Set<Long> practicedVariants(List<VariantQuestion> variants) {
        if (variants.isEmpty()) return Set.of();
        List<Long> ids = variants.stream().map(VariantQuestion::getId).toList();
        Set<Long> result = new HashSet<>();
        for (PracticeRecord r : practiceRecordMapper.selectList(new LambdaQueryWrapper<PracticeRecord>()
                .eq(PracticeRecord::getUserId, UserContext.getUserId())
                .in(PracticeRecord::getVariantId, ids))) result.add(r.getVariantId());
        return result;
    }
}
