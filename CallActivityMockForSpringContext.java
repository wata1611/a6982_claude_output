package org.camunda.community.mockito.process;

import org.camunda.bpm.engine.delegate.JavaDelegate;

/**
 * Implementation that registers the delegates mocks for the mocked subprocess to a registry.
 */
public class CallActivityMockForSpringContext extends CallActivityMock {

  /** Registry where all the mocks will be placed to */
  private SingletonBeanRegistryAdapter springBeanRegistry;

  /**
   * Interface to abstract the singleton bean registration.
   */
  public interface SingletonBeanRegistryAdapter {
    void registerSingleton(String name, Object singleton);
  }

  /**
   * @param processId Process definition key of the subprocess to mock. This should be the value of the 'called element' attribute of the
   *   mocked CallActivity element.
   * @param modelConfigurer Object that allows to customize the mock process model for the subprocess
   * @param springBeanRegistry Adapter to place the implementations of the activities in the mocked process to
   */
  public CallActivityMockForSpringContext(final String processId, final MockedModelConfigurer modelConfigurer,
    final SingletonBeanRegistryAdapter springBeanRegistry) {
    super(processId, modelConfigurer);
    this.springBeanRegistry = springBeanRegistry;
  }

  /**
   * Constructor that does not allow for customizing of the mocked subprocess model
   */
  public CallActivityMockForSpringContext(final String processId, final SingletonBeanRegistryAdapter springBeanRegistry) {
    this(processId, null, springBeanRegistry);
  }

  public SingletonBeanRegistryAdapter getSpringBeanRegistry() {
    return springBeanRegistry;
  }

  @Override
  protected void registerJavaDelegateMock(String delegateReferenceName, JavaDelegate delegate) {
    // Since mock delegate names are generated as random strings, we don't have to unregister an existing bean
    springBeanRegistry.registerSingleton(delegateReferenceName, delegate);
  }

}
