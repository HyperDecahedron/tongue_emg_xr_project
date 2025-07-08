using UnityEditor;
using UnityEngine;

[CustomEditor(typeof(TaskManager))]
public class InspectorButtons : Editor
{
    public override void OnInspectorGUI()
    {
        DrawDefaultInspector(); // Draw the default inspector

        TaskManager controller = (TaskManager)target;

        GUILayout.Space(10);
        GUILayout.Label("User Testing Controls", EditorStyles.boldLabel);

        if (GUILayout.Button("Start Task 1A"))
        {
            controller.StartTask1A();
        }

        if (GUILayout.Button("Start Task 1B"))
        {
            controller.StartTask1B();
        }

        if (GUILayout.Button("Start Task 2A"))
        {
            controller.StartTask2A();
        }

        if (GUILayout.Button("Start Task 2B"))
        {
            controller.StartTask2B();
        }
    }
}
