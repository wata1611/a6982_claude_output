package org.camunda.community.mockito.spring;

import static org.assertj.core.api.Assertions.fail;

import org.camunda.bpm.engine.delegate.DelegateExecution;
import org.camunda.bpm.engine.delegate.ExecutionListener;

public abstract class SpringListeners implements ExecutionListener {

  @Override
  public void notify(DelegateExecution delegateExecution) throws Exception {
    fail(this.getClass().getSimpleName() + ": not implemented!");
  }

  public static class SpringComponentListener extends SpringListeners {};

  public static class SpringNamedComponentListener extends SpringListeners {};

  public static class SpringServiceListener extends SpringListeners {};

  public static class SpringNamedServiceListener extends SpringListeners {};

}
