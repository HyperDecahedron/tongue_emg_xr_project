using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using TMPro;

public class TaskManager : MonoBehaviour
{
    [SerializeField] private TextMeshProUGUI startText;
    [SerializeField] private GameObject startPanel;
    [SerializeField] private GameObject XROrigin;
    [SerializeField] private Transform XROrigin_DesiredPosition;

    [Header("Tasks")]
    [SerializeField] private Task1A task1A;
    [SerializeField] private Task1B task1B;
    [SerializeField] private Task1C task1C;
    [SerializeField] private Task2A task2A;
    [SerializeField] private Task2B task2B;

    private string task = "";

    private void Start()
    {
        startPanel.SetActive(true);
        startText.gameObject.SetActive(true);

        // Hide all tasks initially
        task1A.Hide();
        task1B.Hide();
        task1C.Hide();
        task2A.Hide();
        task2B.Hide();
    }

    public void StartTask1A()
    {
        Debug.Log("Starting task 1A");
        task = "1A";
        StartCoroutine(Do321_count());
    }

    public void StartTask1B()
    {
        Debug.Log("Starting task 1B");
        task = "1B";
        StartCoroutine(Do321_count());
    }

    public void StartTask1C()
    {
        Debug.Log("Starting task 1C");
        task = "1C";
        StartCoroutine(Do321_count());
    }

    public void StartTask2A()
    {
        Debug.Log("Starting task 2A");
        task = "2A";
        StartCoroutine(Do321_count());
    }

    public void StartTask2B()
    {
        Debug.Log("Starting task 2B");
        task = "2B";
        StartCoroutine(Do321_count());
    }

    private IEnumerator Do321_count()
    {
        startPanel.SetActive(true);
        startText.gameObject.SetActive(true);

        string[] countdown = { "3", "2", "1", "Go!" };

        foreach (string count in countdown)
        {
            startText.text = count;
            yield return new WaitForSeconds(1f);
        }

        startText.gameObject.SetActive(false);
        startPanel.SetActive(false);

        switch (task)
        {
            case "1A":
                task1A.Show();
                task1A.StartTask();
                break;

            case "1B":
                task1B.Show();
                task1B.StartTask();
                break;

            case "1C":
                task1C.Show();
                task1C.StartTask();
                break;

            case "2A":
                task2A.Show();
                task2A.StartTask();
                break;

            case "2B":
                task2B.Show();
                task2B.StartTask();
                break;
        }
    }

    public void IntermediatePanel()
    {
        startPanel.SetActive(true);
        startText.gameObject.SetActive(true);
        startText.text = "Good job!\nWait for the next task.";
    }

    public void SkipCurrentTask()
    {
        switch (task)
        {
            case "1A":
                task1A.FinishTask();
                break;

            case "1B":
                task1B.FinishTask();
                break;

            case "1C":
                task1C.FinishTask();
                break;

            case "2A":
                task2A.FinishTask();
                break;

            case "2B":
                task2B.FinishTask();
                break;
        }
    }

    public void TeleportXROrigin()
    {
        if (XROrigin == null || XROrigin_DesiredPosition == null)
        {
            Debug.LogWarning("XR Origin or Desired Position is not assigned.");
            return;
        }

        // Move position
        XROrigin.transform.position = XROrigin_DesiredPosition.position;

        // Match rotation (usually just Y rotation matters in XR)
        Vector3 newEulerAngles = new Vector3(0, XROrigin_DesiredPosition.eulerAngles.y, 0);
        XROrigin.transform.rotation = Quaternion.Euler(newEulerAngles);
    }

}
